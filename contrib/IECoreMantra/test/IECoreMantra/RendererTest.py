##########################################################################
#
#  Copyright 2012, Electric Theatre Collective Limited. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import subprocess
import unittest

import IECore 
import IECoreMantra

_dir = os.path.dirname( __file__ )

class RendererTest( unittest.TestCase ):
	
	def __greenSquare( self, r ):
		r.shader( "surface", "constant", { "Cd": IECore.V3fData( IECore.V3f( 0, 1, 0 ) ) } )
		r.mesh(
			IECore.IntVectorData( [ 4, 4 ] ),
			IECore.IntVectorData( [ 0, 1, 2, 3, 3, 2, 4, 5 ] ), 
			"linear", 
			{ 
				"P" :IECore.PrimitiveVariable(
						IECore.PrimitiveVariable.Interpolation.Vertex,
						IECore.V3fVectorData( [ IECore.V3f( 0, 0, 0 ), IECore.V3f( 0, 1, 0 ), 
												IECore.V3f( 1, 1, 0 ), IECore.V3f( 1, 0, 0 ), 
												IECore.V3f( 2, 1, 0 ), IECore.V3f( 2, 0, 0 ) ] ) 
				)
			}
		)

	def testTypeId( self ):
		self.assertEqual( IECoreMantra.Renderer().typeId(), IECoreMantra.Renderer.staticTypeId() )
		self.assertNotEqual( IECoreMantra.Renderer.staticTypeId(), IECore.Renderer.staticTypeId() )

	def testTypeName( self ):
		r = IECoreMantra.Renderer()
		self.assertEqual( r.typeName(), "IECoreMantra::Renderer" )
		
	def testWorldMesh( self ):
		# test that the ieworld procedural picks up the cache file written by worldEnd() and renders correctly
		r = IECoreMantra.Renderer()
		r.display( 
			_dir + "/output/testWorldMesh.tif" , 
			"tiff", 
			"rgba", 
			{ "variable": "Cf+Af", "vextype": "vector4", "channel": "C" } 
		)
		m = IECore.M44f().translate( IECore.V3f(0,0,6) )
		r.camera( "main", { "projection": "perspective", "transform": m } )
		r.worldBegin()
		self.__greenSquare( r )
		r.worldEnd()
		del r

		imageCreated = IECore.Reader.create( _dir + "/output/testWorldMesh.tif" ).read()
		expectedImage = IECore.Reader.create( _dir + "/data/testWorldMesh.tif" ).read()
		self.assertEqual( 
			IECore.ImageDiffOp()( imageA=imageCreated, imageB=expectedImage, maxError=0.01 ), 
			IECore.BoolData( False ) 
		)
	
	def testIfdGen( self ):
		# the image generated by this scene should be identical to the output of testWorldMesh()
		ifd = _dir + "/output/testIfdGen.ifd"	
		r = IECoreMantra.Renderer( ifd )
		r. display( 
			_dir + "/output/testIfdGen.tif", 
			"tiff", 
			"rgba", 
			{ "variable": "Cf+Af", "vextype": "vector4", "channel": "C" } 
		)
		m = IECore.M44f().translate( IECore.V3f(0,0,6) )
		r.camera( "main", { "projection": "perspective", "transform": m } )
		r.worldBegin()
		self.__greenSquare( r )
		r.worldEnd()
		del r

		self.assertTrue( os.path.isfile( ifd ) )
		
		p = subprocess.Popen( ['mantra'], stdin=open( ifd ), stdout=subprocess.PIPE)
		p.communicate()

		imageCreated = IECore.Reader.create( _dir + "/output/testIfdGen.tif" ).read()
		expectedImage = IECore.Reader.create( _dir + "/data/testWorldMesh.tif" ).read()
		self.assertEqual( 
			IECore.ImageDiffOp()( imageA=imageCreated, imageB=expectedImage, maxError=0.01 ), 
			IECore.BoolData( False ) 
		)

	def __renderGeometry( self ):
		r = IECoreMantra.Renderer()
		r.display( 
			_dir + "/output/testGeometry.tif", 
			"tiff", 
			"rgba",
			{ "variable": "Cf+Af", "vextype": "vector4", "channel": "C" } 
		)
		m = IECore.M44f().translate( IECore.V3f(0,0,6) )
		r.camera( "main", { "projection": "perspective", "transform": m } )
		r.worldBegin()
		r.geometry( 
			"ieprocedural", 
			{"className": "sphereProcedural", "classVersion": 1, "parameterString": ""}, 
			{}
		)
		r.worldEnd()
		del r
	
	def testGeometry( self ):
		self.__renderGeometry()
		imageCreated = IECore.Reader.create( _dir + "/output/testGeometry.tif" ).read()
		expectedImage = IECore.Reader.create( _dir + "/data/testGeometry.tif" ).read()
		self.assertEqual( 
			IECore.ImageDiffOp()( imageA=imageCreated, imageB=expectedImage, maxError=0.01 ), 
			IECore.BoolData( False ) 
		)
	
	def testVrayIncludes( self ):
		# test that mantra can find VRAY_ieProcedural.so and VRAY_ieWorld.so
		p = subprocess.Popen( ['mantra', '-V8'], stdin=open('/dev/null'), stdout=subprocess.PIPE )
		out = p.communicate()[0]
		self.assertTrue( out )
		self.failUnless( "Registering procedural 'ieprocedural'" in out )
		self.failUnless( "Registering procedural 'ieworld'" in out )

	def testOptions( self ):
		ifd = _dir + "/output/testOptions.ifd"
		r = IECoreMantra.Renderer( ifd )
		r.setOption( "itest", IECore.IntData(42) );
		r.setOption( "ftest", IECore.FloatData(1.23) );
		r.setOption( "v3ftest", IECore.V3f(1,0,0) );
		r.setOption( "stringtest", IECore.StringData("hello") );
		r.worldBegin()
		r.worldEnd()
		del r
		l = "".join( file( ifd ).readlines() ).replace( "\n", "" )
		self.failUnless( 'ray_declare global int itest 42' in l )
		self.failUnless( 'ray_declare global float ftest 1.23' in l )
		self.failUnless( 'ray_declare global vector3 v3ftest 1 0 0' in l )
		self.failUnless( 'ray_declare global string stringtest "hello"' in l )
	
	def testShaderParameters( self ):
		# Test the shader parameters end up in the scene.. you would expect them in
		# ifd but because everything post-world is stored in a side-car .cob file
		# we look for that instead and check the shader invocation string is on the 
		# top of the render state.
		ifd = _dir + "/output/testShaderParameters.ifd"
		r = IECoreMantra.Renderer( ifd )
		r.worldBegin()
		r.shader("surface", "testshader", 
					{
						"p1": IECore.IntData(11), 
						"p2": IECore.FloatData(1.234), 
						"p3": IECore.StringData("hello"),
						"p4": IECore.V3fData( IECore.V3f(1,2,3) ),
						"p5": IECore.Color3fData( IECore.Color3f(1,0,0) ),
					}
				)
		r.worldEnd()
		del r
		self.failUnless( os.path.exists( ifd ) )
		self.failUnless( os.path.exists( ifd + ".ieworld.cob" ) )
		world = IECore.Reader.create( ifd + ".ieworld.cob" ).read()
		self.assertTrue( world )
		self.assertEquals( world.typeId(), IECore.Group.staticTypeId() )
		self.assertTrue( world.state() )
		self.assertEquals( 
			world.state()[0].attributes[':surface'], 
			IECore.StringData( 'testshader p2 1.234 p3 "hello" p1 11 p4 1 2 3 p5 1 0 0 ')
		)
	
	def tearDown( self ):
		files = [
				_dir + "/output/testGeometry.tif",
				_dir + "/output/testWorldMesh.tif",
				_dir + "/output/testIfdGen.tif",
				_dir + "/output/testIfdGen.ifd",
				_dir + "/output/testIfdGen.ifd.ieworld.cob",
				_dir + "/output/testOptions.ifd",
				_dir + "/output/testOptions.ifd.ieworld.cob",
				_dir + "/output/testShaderParameters.ifd",
				_dir + "/output/testShaderParameters.ifd.ieworld.cob",
				]
		for f in files:
			if os.path.exists( f ):
				os.remove( f )

if __name__ == "__main__":
	unittest.main()
				
