##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import unittest

import hou

import IECore
import IECoreHoudini

class HoudiniSceneTest( IECoreHoudini.TestCase ) :
	
	def testFactory( self ) :
		
		scene = IECore.SceneInterface.create( "x.hip", IECore.IndexedIO.OpenMode.Read )
		self.failUnless( isinstance( scene, IECoreHoudini.HoudiniScene ) )
		self.assertEqual( scene.typeId(), IECoreHoudini.TypeId.HoudiniScene )
	
	def buildScene( self ) :
		
		obj = hou.node( "/obj" )
		sub1 = obj.createNode( "subnet", "sub1" )
		sub2 = obj.createNode( "subnet", "sub2" )
		box1 = sub1.createOutputNode( "geo", "box1", run_init_scripts=False )
		box1.createNode( "box", "actualBox" )
		actualBox = box1.children()[0]
		bname = actualBox.createOutputNode( "name" )
		bname.parm( "name1" ).set( "/sub1/box1" )
		torus = box1.createNode( "torus" )
		tname = torus.createOutputNode( "name" )
		tname.parm( "name1" ).set( "/sub1/box1/torus" )
		merge = bname.createOutputNode( "merge" )
		merge.setInput( 1, tname )
		merge.setRenderFlag( True )
		box2 = obj.createNode( "geo", "box2", run_init_scripts=False )
		box2.createNode( "box", "actualBox" )
		torus1 = sub1.createNode( "geo", "torus1", run_init_scripts=False )
		torus1.createNode( "torus", "actualTorus" )
		torus2 = torus1.createOutputNode( "geo", "torus2", run_init_scripts=False )
		torus2.createNode( "torus", "actualTorus" )
		
		return IECoreHoudini.HoudiniScene()
	
	def testChildNames( self ) :
	
		scene = self.buildScene()
		self.assertEqual( sorted( scene.childNames() ), [ "box2", "sub1", "sub2" ] )
		
		child = scene.child( "sub1" )
		self.assertEqual( sorted( child.childNames() ), [ "box1", "torus1" ] )
		
		child2 = child.child( "torus1" )
		self.assertEqual( sorted( child2.childNames() ), [ "torus2" ] )
		
		child3 = child2.child( "torus2" )
		self.assertEqual( sorted( child3.childNames() ), [] )
		
		box1 = child.child( "box1" )
		self.assertEqual( sorted( box1.childNames() ), [ "torus" ] )
		
		self.assertEqual( box1.child( "torus" ).childNames(), [] )
		self.assertEqual( scene.child( "box2" ).childNames(), [] )
		self.assertEqual( scene.child( "sub2" ).childNames(), [] )
	
	def testHasChild( self ) :
		
		scene = self.buildScene()
		self.assertEqual( scene.hasChild( "box2" ), True )
		self.assertEqual( scene.hasChild( "sub1" ), True )
		self.assertEqual( scene.hasChild( "sub2" ), True )
		self.assertEqual( scene.hasChild( "fake" ), False )
		
		child = scene.child( "sub1" )
		self.assertEqual( child.hasChild( "torus1" ), True )
		self.assertEqual( child.hasChild( "torus2" ), False )
		self.assertEqual( child.child( "torus1" ).hasChild( "torus2" ), True )
		self.assertEqual( child.hasChild( "fake" ), False )
		
		self.assertEqual( child.hasChild( "box1" ), True )
		self.assertEqual( child.child( "box1" ).hasChild( "torus" ), True )
	
	def testNames( self ) :
		
		scene = self.buildScene()
		self.assertEqual( scene.name(), "/" )
		self.assertEqual( scene.child( "box2" ).name(), "box2" )
		self.assertEqual( scene.child( "sub2" ).name(), "sub2" )
		
		sub1 = scene.child( "sub1" )
		self.assertEqual( sub1.name(), "sub1" )
		self.assertEqual( sub1.child( "box1" ).name(), "box1" )
		self.assertEqual( sub1.child( "box1" ).child( "torus" ).name(), "torus" )
		
		torus1 = sub1.child( "torus1" )
		self.assertEqual( torus1.name(), "torus1" )
		self.assertEqual( torus1.child( "torus2" ).name(), "torus2" )
	
	def testPaths( self ) :
		
		scene = self.buildScene()
		self.assertEqual( scene.path(), [] )
		self.assertEqual( scene.pathAsString(), "/" )
		self.assertEqual( scene.child( "box2" ).path(), [ "box2" ] )
		self.assertEqual( scene.child( "box2" ).pathAsString(), "/box2" )
		self.assertEqual( scene.child( "sub2" ).path(), [ "sub2" ] )
		self.assertEqual( scene.child( "sub2" ).pathAsString(), "/sub2" )
		
		sub1 = scene.child( "sub1" )
		self.assertEqual( sub1.path(), [ "sub1" ] )
		self.assertEqual( sub1.pathAsString(), "/sub1" )
		self.assertEqual( sub1.child( "box1" ).path(), [ "sub1", "box1" ] )
		self.assertEqual( sub1.child( "box1" ).pathAsString(), "/sub1/box1" )
		self.assertEqual( sub1.child( "box1" ).child( "torus" ).path(), [ "sub1", "box1", "torus" ] )
		self.assertEqual( sub1.child( "box1" ).child( "torus" ).pathAsString(), "/sub1/box1/torus" )
		
		torus1 = sub1.child( "torus1" )
		self.assertEqual( torus1.path(), [ "sub1", "torus1" ] )
		self.assertEqual( torus1.pathAsString(), "/sub1/torus1" )
		self.assertEqual( torus1.child( "torus2" ).path(), [ "sub1", "torus1", "torus2" ] )
		self.assertEqual( torus1.child( "torus2" ).pathAsString(), "/sub1/torus1/torus2" )
		
		## \todo: add a harder test. 3 connections at the same level, and 3 one level deep
		
		self.assertRaises( RuntimeError, scene.child, "idontexist" )
		self.assertEqual( scene.child( "idontexist", IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )
		
		# test the node that does exist according to houdini, but is actually a grandchild in our world
		self.assertRaises( RuntimeError, scene.child, "box1" )
		self.assertEqual( scene.child( "box1", IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )		
		
	def testSceneMethod( self ) :
		
		scene = self.buildScene()
		
		self.assertEqual( scene.scene( [ "sub2" ] ).pathAsString(), "/sub2" )
		
		torus1 = scene.scene( [ "sub1", "torus1" ] )
		self.assertEqual( torus1.name(), "torus1" )
		self.assertEqual( torus1.path(), [ "sub1", "torus1" ] )
		self.assertEqual( torus1.pathAsString(), "/sub1/torus1" )
		self.assertEqual( torus1.hasChild( "torus2" ), True )
		self.assertEqual( torus1.childNames(), [ "torus2" ] )
		
		# does it still return absolute paths if we've gone to another location?
		sub1 = scene.scene( [ "sub1" ] )
		self.assertEqual( sub1.scene( [] ).name(), "/" )
		self.assertEqual( sub1.scene( [ "sub1", "torus1", "torus2" ] ).pathAsString(), "/sub1/torus1/torus2" )
		self.assertEqual( sub1.scene( [ "box2" ] ).pathAsString(), "/box2" )
		
		self.assertRaises( RuntimeError, scene.scene, [ "idontexist" ] )
		self.assertEqual( scene.scene( [ "idontexist" ], IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )
		
		# test the node that does exist according to houdini, but is actually a grandchild in our world
		self.assertRaises( RuntimeError, scene.scene, [ "box1" ] )
		self.assertEqual( scene.scene( [ "box1" ], IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )

	def testHasObject( self ) :
		
		scene = self.buildScene()
		self.assertEqual( scene.hasObject(), False )
		self.assertEqual( scene.child( "box2" ).hasObject(), True )
		self.assertEqual( scene.child( "sub2" ).hasObject(), False )
		
		sub1 = scene.child( "sub1" )
		self.assertEqual( sub1.hasObject(), False )
		torus1 = sub1.child( "torus1" )
		self.assertEqual( torus1.hasObject(), True )
		self.assertEqual( torus1.child( "torus2" ).hasObject(), True )
		self.assertEqual( sub1.child( "box1" ).hasObject(), True )
		self.assertEqual( sub1.child( "box1" ).child( "torus" ).hasObject(), True )
	
	def testDeletedPath( self ) :
		
		scene = self.buildScene()
		sub1 = scene.child( "sub1" )
		torus1 = sub1.child( "torus1" )
		
		hou.node( "/obj/sub1/torus1" ).destroy()
		
		self.assertRaises( RuntimeError, IECore.curry( torus1.scene, [ "sub1", "torus1" ] ) )
		self.assertEqual( torus1.scene( [ "sub1", "torus1" ], IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )
		self.assertRaises( RuntimeError, IECore.curry( torus1.child, "torus2" ) )
		self.assertEqual( torus1.child( "torus2", IECore.SceneInterface.MissingBehaviour.NullIfMissing ), None )
		self.assertRaises( RuntimeError, torus1.childNames )
		self.assertRaises( RuntimeError, torus1.path )
		self.assertRaises( RuntimeError, torus1.hasObject )
		self.assertRaises( RuntimeError, IECore.curry( torus1.readBound, 0.0 ) )
		self.assertRaises( RuntimeError, IECore.curry( torus1.readObject, 0.0 ) )
		self.assertRaises( RuntimeError, IECore.curry( torus1.readTransform, 0.0 ) )
		self.assertRaises( RuntimeError, IECore.curry( torus1.readTransformAsMatrix, 0.0 ) )
	
	def testReadMesh( self ) :
		
		scene = self.buildScene()
		hou.node( "/obj/sub1" ).parmTuple( "t" ).set( [ 1, 2, 3 ] )
		hou.node( "/obj/sub1" ).parmTuple( "r" ).set( [ 10, 20, 30 ] )
		
		box1 = scene.child( "sub1" ).child( "box1" )
		mesh = box1.readObject( 0 )
		self.failUnless( isinstance( mesh, IECore.MeshPrimitive ) )
		
		vertList = list( mesh["P"].data )
		self.assertEqual( len( vertList ), 8 )
		
		# check the verts are in local space
		self.assertEqual( vertList.count( IECore.V3f( -0.5, -0.5, 0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( 0.5, -0.5, 0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( -0.5, 0.5, 0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( 0.5, 0.5, 0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( -0.5, 0.5, -0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( 0.5, 0.5, -0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( -0.5, -0.5, -0.5 ) ), 1 )
		self.assertEqual( vertList.count( IECore.V3f( 0.5, -0.5, -0.5 ) ), 1 )
	
	def testAnimatedMesh( self ) :
		
		scene = self.buildScene()
		shape = hou.node( "/obj/box1/actualBox" )
		deformer = shape.createOutputNode( "twist" )
		deformer.parm( "paxis" ).set( 1 )
		deformer.parm( "strength" ).setExpression( "10*$T" )
		
		box1 = scene.child( "sub1" ).child( "box1" )
		mesh0   = box1.readObject( 0 )
		mesh0_5 = box1.readObject( 0.5 )
		mesh1   = box1.readObject( 1 )
		# the mesh hasn't moved because the deformer isn't the renderable SOP
		self.assertEqual( mesh0, mesh0_5 )
		self.assertEqual( mesh0, mesh1 )
		self.assertEqual( len(mesh0["P"].data), 8 )
		self.assertEqual( mesh0["P"].data[0].x, -0.5 )
		self.assertEqual( mesh0_5["P"].data[0].x, -0.5 )
		self.assertEqual( mesh1["P"].data[0].x, -0.5 )
		
		deformer.setRenderFlag( True )
		mesh0   = box1.readObject( 0 )
		mesh0_5 = box1.readObject( 0.5 )
		mesh1   = box1.readObject( 1 )
		self.assertEqual( len(mesh0["P"].data), 8 )
		self.assertEqual( len(mesh0_5["P"].data), 8 )
		self.assertEqual( len(mesh1["P"].data), 8 )
		self.assertEqual( mesh0["P"].data[0].x, -0.5 )
		self.assertAlmostEqual( mesh0_5["P"].data[0].x, -0.521334, 6 )
		self.assertAlmostEqual( mesh1["P"].data[0].x, -0.541675, 6 )
	
	def testReadBound( self ) :
		
		scene = self.buildScene()
		hou.node( "/obj/sub1" ).parmTuple( "t" ).set( [ 1, 1, 1 ] )
		hou.node( "/obj/sub1/torus1" ).parmTuple( "t" ).set( [ 2, 2, 2 ] )
		hou.node( "/obj/sub1/torus2" ).parmTuple( "t" ).set( [ -1, 0, 2 ] )
		hou.node( "/obj/box1" ).parmTuple( "t" ).set( [ -1, -1, -1 ] )
		# to make the bounds nice round numbers
		hou.node( "/obj/sub1/torus1/actualTorus" ).parm( "rows" ).set( 100 )
		hou.node( "/obj/sub1/torus1/actualTorus" ).parm( "cols" ).set( 100 )
		hou.node( "/obj/sub1/torus2/actualTorus" ).parm( "rows" ).set( 100 )
		hou.node( "/obj/sub1/torus2/actualTorus" ).parm( "cols" ).set( 100 )
		
		self.assertEqual( scene.child( "box2" ).readBound( 0 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		
		sub1 = scene.child( "sub1" )
		box1 = sub1.child( "box1" )
		self.assertEqual( box1.readBound( 0 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		
		torus1 = sub1.child( "torus1" )
		torus2 = torus1.child( "torus2" )
		self.assertEqual( torus2.readBound( 0 ), IECore.Box3d( IECore.V3d( -1.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 1.5 ) ) )
		self.assertEqual( torus1.readBound( 0 ), IECore.Box3d( IECore.V3d( -2.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 3.5 ) ) )
		self.assertEqual( sub1.readBound( 0 ), IECore.Box3d( IECore.V3d( -1.5 ), IECore.V3d( 3.5, 2.5, 5.5 ) ) )
		self.assertEqual( scene.readBound( 0 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 4.5, 3.5, 6.5 ) ) )
		
	def testAnimatedBound( self ) :
		
		scene = self.buildScene()
		hou.node( "/obj/sub1" ).parmTuple( "t" ).set( [ 1, 1, 1 ] )
		hou.node( "/obj/sub1/torus1" ).parm( "tx" ).setExpression( "$T" )
		hou.node( "/obj/sub1/torus1" ).parm( "ty" ).setExpression( "$T" )
		hou.node( "/obj/sub1/torus1" ).parm( "tz" ).setExpression( "$T" )
		hou.node( "/obj/sub1/torus2" ).parmTuple( "t" ).set( [ -1, 0, 2 ] )
		hou.node( "/obj/box1" ).parm( "tx" ).setExpression( "-$T" )
		hou.node( "/obj/box1" ).parm( "ty" ).setExpression( "-$T" )
		hou.node( "/obj/box1" ).parm( "tz" ).setExpression( "-$T" )
		# to make the bounds nice round numbers
		hou.node( "/obj/sub1/torus1/actualTorus" ).parm( "rows" ).set( 100 )
		hou.node( "/obj/sub1/torus1/actualTorus" ).parm( "cols" ).set( 100 )
		hou.node( "/obj/sub1/torus2/actualTorus" ).parm( "rows" ).set( 100 )
		hou.node( "/obj/sub1/torus2/actualTorus" ).parm( "cols" ).set( 100 )
		
		self.assertEqual( scene.child( "box2" ).readBound( 0 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		
		sub1 = scene.child( "sub1" )
		box1 = sub1.child( "box1" )
		self.assertEqual( box1.readBound( 0 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		
		torus1 = sub1.child( "torus1" )
		torus2 = torus1.child( "torus2" )
		self.assertEqual( torus2.readBound( 0 ), IECore.Box3d( IECore.V3d( -1.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 1.5 ) ) )
		self.assertEqual( torus1.readBound( 0 ), IECore.Box3d( IECore.V3d( -2.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 3.5 ) ) )
		self.assertEqual( sub1.readBound( 0 ), IECore.Box3d( IECore.V3d( -2.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 3.5 ) ) )
		self.assertEqual( scene.readBound( 0 ), IECore.Box3d( IECore.V3d( -1.5, -0.5, -0.5 ), IECore.V3d( 2.5, 1.5, 4.5 ) ) )
		
		# time 1
		self.assertEqual( box1.readBound( 1 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		self.assertEqual( torus2.readBound( 1 ), IECore.Box3d( IECore.V3d( -1.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 1.5 ) ) )
		self.assertEqual( torus1.readBound( 1 ), IECore.Box3d( IECore.V3d( -2.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 3.5 ) ) )
		self.assertEqual( sub1.readBound( 1 ), IECore.Box3d( IECore.V3d( -1.5 ), IECore.V3d( 2.5, 1.5, 4.5 ) ) )
		self.assertEqual( scene.readBound( 1 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 3.5, 2.5, 5.5 ) ) )
		
		# time 1.5
		self.assertEqual( box1.readBound( 1.5 ), IECore.Box3d( IECore.V3d( -0.5 ), IECore.V3d( 0.5 ) ) )
		self.assertEqual( torus2.readBound( 1.5 ), IECore.Box3d( IECore.V3d( -1.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 1.5 ) ) )
		self.assertEqual( torus1.readBound( 1.5 ), IECore.Box3d( IECore.V3d( -2.5, -0.5, -1.5 ), IECore.V3d( 1.5, 0.5, 3.5 ) ) )
		self.assertEqual( sub1.readBound( 1.5 ), IECore.Box3d( IECore.V3d( -2 ), IECore.V3d( 3, 2, 5 ) ) )
		self.assertEqual( scene.readBound( 1.5 ), IECore.Box3d( IECore.V3d( -1 ), IECore.V3d( 4, 3, 6 ) ) )
	
	def testReadTransformMethods( self ) :
		
		scene = self.buildScene()
		hou.node( "/obj/sub1/torus1" ).parmTuple( "t" ).set( [ 1, 2, 3 ] )
		hou.node( "/obj/sub1/torus1" ).parmTuple( "r" ).set( [ 10, 20, 30 ] )
		hou.node( "/obj/sub1/torus1" ).parmTuple( "s" ).set( [ 4, 5, 6 ] )
		
		torus1 = scene.child( "sub1" ).child( "torus1" )
		transform = torus1.readTransform( 0 ).value
		
		self.assertEqual( transform.translate.x, 1 )
		self.assertEqual( transform.translate.y, 2 )
		self.assertEqual( transform.translate.z, 3 )
		self.assertAlmostEqual( IECore.radiansToDegrees( transform.rotate.x ), 10.0, 5 )
		self.assertAlmostEqual( IECore.radiansToDegrees( transform.rotate.y ), 20.0, 5 )
		self.assertAlmostEqual( IECore.radiansToDegrees( transform.rotate.z ), 30.0, 5 )
		self.assertAlmostEqual( transform.scale.x, 4, 6 )
		self.assertAlmostEqual( transform.scale.y, 5, 6 )
		self.assertAlmostEqual( transform.scale.z, 6, 6 )
		self.failUnless( torus1.readTransformAsMatrix( 0 ).equalWithAbsError( transform.transform, 1e-6 ) )
	
	def testAnimatedTransform( self ) :
		
		scene = self.buildScene()
		hou.node( "/obj/sub1/torus1" ).parm( "tx" ).setExpression( "$T" )
		hou.node( "/obj/sub1/torus1" ).parm( "ty" ).setExpression( "$T+1" )
		hou.node( "/obj/sub1/torus1" ).parm( "tz" ).setExpression( "$T+2" )
		
		torus1 = scene.child( "sub1" ).child( "torus1" )
		transform0 = torus1.readTransform( 0 ).value
		transform0_5 = torus1.readTransform( 0.5 ).value
		transform1 = torus1.readTransform( 1 ).value
		
		self.assertEqual( transform0.translate, IECore.V3d( 0, 1, 2 ) )
		self.assertAlmostEqual( transform0_5.translate.x, 0.5, 5 )
		self.assertAlmostEqual( transform0_5.translate.y, 1.5, 5 )
		self.assertAlmostEqual( transform0_5.translate.z, 2.5, 5 )
		self.assertEqual( transform1.translate, IECore.V3d( 1, 2, 3 ) )

if __name__ == "__main__":
	unittest.main()
