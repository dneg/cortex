##########################################################################
#
#  Copyright (c) 2008-2010, Image Engine Design Inc. All rights reserved.
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

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import unittest, MayaUnitTest
import os.path
import IECore
import IECoreMaya


class TestParameterisedHolder( unittest.TestCase ) :

	def testNode( self ):
		""" Test ParameterisedHolderNode """
		n = cmds.createNode( "ieParameterisedHolderNode" )
		h = IECoreMaya.FnParameterisedHolder( str(n) )
		self.assert_( h )

		p = IECore.ParticleMeshOp()

		h.setParameterised( p )

		p.parameters()["filename"] = "testValue"
		h.setNodeValue( p.parameters()["filename"] )
		pl = h.parameterPlug( p.parameters()["filename"] )
		v = IECoreMaya.FromMayaPlugConverter.create( pl, IECore.TypeId.StringData ).convert()
		self.assertEqual( v.value, "testValue" )

		cmds.setAttr( pl.name(), "testValue2", typ="string" )
		h.setParameterisedValue( p.parameters()["filename"] )
		self.assertEqual( p.parameters()["filename"].getValue().value, "testValue2" )


	def testParameterisedHolderSetReference( self ):
		""" Test multiple references to ieParameterisedHolderSet nodes """

		nodeType = "ieParameterisedHolderSet"

		nodeName = cmds.createNode( nodeType )

		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "reference.ma" ) )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )

		cmds.file( new = True, force = True )
		cmds.file( scene, reference = True, namespace = "ns1" )
		cmds.file( scene, reference = True, namespace = "ns2" )

		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "referenceMaster.ma" ) )
		masterScene = cmds.file( force = True, type = "mayaAscii", save = True )

		cmds.file( masterScene, force = True, open = True )

		nodeName1 = "ns1:" + nodeName
		nodeName2 = "ns2:" + nodeName

		l = OpenMaya.MSelectionList()
		l.add( nodeName1 )
		l.add( nodeName2 )

		node1 = OpenMaya.MObject()
		l.getDependNode( 0, node1 )
		node2 = OpenMaya.MObject()
		l.getDependNode( 1, node2 )

		fn1 = OpenMaya.MFnDependencyNode( node1 )
		fn2 = OpenMaya.MFnDependencyNode( node2 )

		self.assert_( fn1.userNode() )
		self.assert_( fn2.userNode() ) # This failure is due to a Maya bug. When referencing the same scene twice, as an optimisation Maya will duplicate existing nodes instead of creating new ones. There is a bug in MPxObjectSet::copy() which gets exercised here. Setting the environment variable MAYA_FORCE_REF_READ to 1 will disable this optimisation, however.

	def testChangeDefault( self ) :
		""" Test that changing parameter defaults is correctly reflected in Maya attributes """

		def makeOp( defaultValue ) :

			class TestOp( IECore.Op ) :

				def __init__( self ) :

					IECore.Op.__init__( self, "Tests stuff",
						IECore.IntParameter(
							name = "result",
							description = "",
							defaultValue = 0
						)
					)

					self.parameters().addParameters(
						[
							IECore.Color3fParameter(
								name = "c",
								description = "",
								defaultValue = defaultValue
							),
						]
					)

			return TestOp()


		n = cmds.createNode( "ieParameterisedHolderNode" )
		h = IECoreMaya.FnParameterisedHolder( str(n) )
		self.assert_( h )

		p = makeOp( IECore.Color3f( 0, 0, 0 ) )
		h.setParameterised( p )
		dv = cmds.attributeQuery ( "parm_c", node = n, listDefault = True )
		self.assertEqual( dv, [ 0, 0, 0 ] )

		p = makeOp( IECore.Color3f( 1, 1, 1 ) )
		h.setParameterised( p )
		dv = cmds.attributeQuery ( "parm_c", node = n, listDefault = True )
		self.assertEqual( dv, [ 1, 1, 1 ] )

	def testDirectSettingOfOp( self ) :
	
		class TestOp( IECore.Op ) :
		
			def __init__( self ) :
			
				IECore.Op.__init__( self,
					"",
					IECore.FloatParameter(
						"result",
						"",
						0.0
					),
				)
				
				self.parameters().addParameter(

					IECore.FloatParameter(
						"a",
						"",
						0.0
					)

				)
				
			def doOperation( self, operands ) :
			
				return IECore.FloatData( operands["a"].value )
				
		node = cmds.createNode( "ieOpHolderNode" )
		fnOH = IECoreMaya.FnParameterisedHolder( str( node ) )

		op = TestOp()
		fnOH.setParameterised( op )
	
		self.failUnless( cmds.objExists( node + ".result" ) )
		
		aAttr = fnOH.parameterPlugPath( op["a"] )

		cmds.setAttr( aAttr, 10 )
		self.assertEqual( cmds.getAttr( node + ".result" ), 10 )

		cmds.setAttr( aAttr, 20 )
		self.assertEqual( cmds.getAttr( node + ".result" ), 20 )


	def testLazySettingFromCompoundPlugs( self ) :
	
		class TestProcedural( IECore.ParameterisedProcedural ) :
		
			def __init__( self ) :
			
				IECore.ParameterisedProcedural.__init__( self, "" )
				
				self.parameters().addParameter(
				
					IECore.V3fParameter(
						"halfSize",
						"",
						IECore.V3f( 0 )
					)
				
				)
				
			def doBound( self, args ) :
			
				return IECore.Box3f( -args["halfSize"].value, args["halfSize"].value )
			
			def doRenderState( self, args ) :
			
				pass
					
			def doRender( self, args ) :
			
				pass
	
		node = cmds.createNode( "ieProceduralHolder" )
		fnPH = IECoreMaya.FnParameterisedHolder( str( node ) )
		
		p = TestProcedural()
		fnPH.setParameterised( p )
		
		self.assertEqual( cmds.getAttr( node + ".boundingBoxMin" ), [( 0, 0, 0 )] )
		cmds.setAttr( fnPH.parameterPlugPath( p["halfSize"] ), 1, 2, 3 )
		
		self.assertEqual( cmds.getAttr( node + ".boundingBoxMin" ), [( -1, -2, -3 )] )
	
	def testLazySettingFromArrayPlugs( self ) :
	
		class TestProcedural( IECore.ParameterisedProcedural ) :
		
			def __init__( self ) :
			
				IECore.ParameterisedProcedural.__init__( self, "" )
				
				self.parameters().addParameter( 
				
					IECore.SplineffParameter(
						"spline",
						"",
						defaultValue = IECore.SplineffData(
							IECore.Splineff(
								IECore.CubicBasisf.catmullRom(),
								(
									( 0, 1 ),
									( 0, 1 ),
									( 1, 0 ),
									( 1, 0 ),
								),
							),
						),
					),
				
				)
				
			def doBound( self, args ) :
			
				v = args["spline"].value.points()[0][1]
			
				return IECore.Box3f( IECore.V3f( -v ), IECore.V3f( v ) )
			
			def doRenderState( self, args ) :
			
				pass
					
			def doRender( self, args ) :
			
				pass
	
		node = cmds.createNode( "ieProceduralHolder" )
		fnPH = IECoreMaya.FnParameterisedHolder( str( node ) )
		
		p = TestProcedural()
		fnPH.setParameterised( p )
		
		self.assertEqual( cmds.getAttr( node + ".boundingBoxMin" ), [( -1, -1, -1 )] )
		
		plugPath = fnPH.parameterPlugPath( p["spline"] )
		plugName = plugPath.partition( "." )[2]
		pointValuePlugPath = plugPath + "[0]." + plugName + "_FloatValue"
		
		cmds.setAttr( pointValuePlugPath, 2 )
		
		self.assertEqual( cmds.getAttr( node + ".boundingBoxMin" ), [( -2, -2, -2 )] )
	
	def testObjectParameterIOProblem( self ) :
	
		fnPH = IECoreMaya.FnProceduralHolder.create( "procedural", "image", 1 )
		p = fnPH.getProcedural()
		
		w = IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 255 ) )
		image = IECore.ImagePrimitive( w, w )
		image.createFloatChannel( "Y" )
		image.createFloatChannel( "A" )
		p.parameters()["image"].setValue( image )
		fnPH.setNodeValues()
		
		cmds.file( rename = os.getcwd() + "/test/IECoreMaya/objectParameterIO.ma" )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )

		cmds.file( new = True, force = True )
		cmds.file( scene, open = True )
		
		fnPH = IECoreMaya.FnProceduralHolder( "proceduralShape" )
		fnPH.setParameterisedValues()
		p = fnPH.getProcedural()
				
		i2 = p.parameters()["image"].getValue()
		
		self.assertEqual( p.parameters()["image"].getValue(), image )
	
	def testOpHolder( self ) :
	
		fnOH = IECoreMaya.FnOpHolder.create( "opHolder", "maths/multiply", 2 )
		op = fnOH.getOp()
		
		self.assertEqual( cmds.attributeQuery( "result", node="opHolder", storable=True ), False )
		self.assertEqual( cmds.attributeQuery( "result", node="opHolder", writable=True ), False )
		
		aPlug = fnOH.parameterPlugPath( op["a"] )
		bPlug = fnOH.parameterPlugPath( op["b"] )
		
		cmds.setAttr( aPlug, 20 )
		cmds.setAttr( bPlug, 100 )
		
		self.failUnless( cmds.getAttr( "opHolder.result" ), 2000 )

	def testParameterTypes( self ) :
	
		node = cmds.createNode( "ieOpHolderNode" )
		fnPH = IECoreMaya.FnParameterisedHolder( node )

		op = IECore.ClassLoader.defaultOpLoader().load( "parameterTypes", 1 )()
		op.parameters().removeParameter( "m" ) # no color4f support in maya

		fnPH.setParameterised( op )
		
		for parameter in op.parameters().values() :
		
			self.failUnless( cmds.objExists( fnPH.parameterPlugPath( parameter ) ) )
		
	def testCompoundObjectConnections( self ) :
	
		fnOHA = IECoreMaya.FnOpHolder.create( "opA", "compoundObjectInOut", 1 )
				
		fnOHB = IECoreMaya.FnOpHolder.create( "opB", "compoundObjectInOut", 1 )
		opB = fnOHB.getOp()
				
		inputPlug = fnOHB.parameterPlugPath( opB["input"] )
		cmds.connectAttr( "opA.result", inputPlug )
		
		self.assertEqual( cmds.listConnections( inputPlug, source=True, destination=False, plugs=True ), [ "opA.result" ] )
		self.assertEqual( cmds.listConnections( inputPlug, source=False, destination=True, plugs=True ), None )
				
		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "compoundObjectConnections.ma" ) )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )
				
		cmds.file( new = True, force = True )
		cmds.file( scene, open = True )
				
		self.assertEqual( cmds.listConnections( inputPlug, source=True, destination=False, plugs=True ), [ "opA.result" ] )
		self.assertEqual( cmds.listConnections( inputPlug, source=False, destination=True, plugs=True ), None )
	
	def testDefaultConnections( self ) :
	
		# make an opholder for an op with default connections
		# and make sure they are made.
	
		fnOH = IECoreMaya.FnOpHolder.create( "opA", "mayaUserData", 1 )
		op = fnOH.getOp()

		tPlug = fnOH.parameterPlugPath( op["t"] )
		
		self.assertEqual( cmds.listConnections( tPlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), [ "time1.outTime" ] )
		self.assertEqual( cmds.listConnections( tPlug, source=False, destination=True, plugs=True ), None )
		
		ePlug = fnOH.parameterPlugPath( op["e"] )
		
		eInputPlugs = cmds.listConnections( ePlug, source=True, destination=False, plugs=True )
		eInputNodes = cmds.listConnections( ePlug, source=True, destination=False )
		self.assertEqual( len( eInputNodes ), 1 )
		self.assertEqual( cmds.nodeType( eInputNodes[0] ), "expression" )
		
		# save the file
		
		cmds.file( rename = os.getcwd() + "/test/IECoreMaya/defaultConnections.ma" )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )

		# load it again and check the connections are still there

		cmds.file( new = True, force = True )
		cmds.file( scene, open = True )

		self.assertEqual( cmds.listConnections( tPlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), [ "time1.outTime" ] )
		self.assertEqual( cmds.listConnections( tPlug, source=False, destination=True, plugs=True ), None )
		
		eInputNodes = cmds.listConnections( ePlug, source=True, destination=False )
		self.assertEqual( len( eInputNodes ), 1 )
		self.assertEqual( cmds.nodeType( eInputNodes[0] ), "expression" )
		
		# remove the connections and save
		
		cmds.disconnectAttr( "time1.outTime", tPlug )
		cmds.disconnectAttr( eInputPlugs[0], ePlug )

		self.assertEqual( cmds.listConnections( tPlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), None )
		self.assertEqual( cmds.listConnections( ePlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), None )
		
		scene = cmds.file( force = True, type = "mayaAscii", save = True )

		# load again and check they remain disconnected
		
		cmds.file( new = True, force = True )
		cmds.file( scene, open = True )

		self.assertEqual( cmds.listConnections( tPlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), None )
		self.assertEqual( cmds.listConnections( ePlug, source=True, destination=False, plugs=True, skipConversionNodes=True ), None )	
	
	def testConnectedNodeNameValueProvider( self ) :
	
		fnOH = IECoreMaya.FnOpHolder.create( "opA", "mayaUserData", 1 )
		op = fnOH.getOp()
		
		fnOH.setParameterisedValues()
		self.assertEqual( op["s"].getTypedValue(), "" )
		
		sPlug = fnOH.parameterPlugPath( op["s"] )
		cmds.connectAttr( "time1.outTime", sPlug )
		
		fnOH.setParameterisedValues()
		self.assertEqual( op["s"].getTypedValue(), "time1" )
		
	def testClassParameter( self ) :
	
		class TestOp( IECore.Op ) :
		
			def __init__( self ) :

				IECore.Op.__init__( self,
					"",
					IECore.FloatParameter(
						"result",
						"",
						0.0
					),
				)
				
				self.parameters().addParameter(

					IECore.ClassParameter(
						"cp",
						"",
						"IECORE_OP_PATHS"
					)

				)
				
			def doOperation( self, operands ) :
			
				return IECore.FloatData( 1 )
				
		node = cmds.createNode( "ieOpHolderNode" )
		fnOH = IECoreMaya.FnParameterisedHolder( str( node ) )

		op = TestOp()
		fnOH.setParameterised( op )
		
		fnOH.setClassParameterClass( op["cp"], "maths/multiply", 1, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( op["cp"]["a"] )
		bPlugPath = fnOH.parameterPlugPath( op["cp"]["b"] )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 1 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 2 )
		
		fnOH.setClassParameterClass( op["cp"], "stringParsing", 1, "IECORE_OP_PATHS" )
		
		self.failIf( cmds.objExists( aPlugPath ) )
		self.failIf( cmds.objExists( bPlugPath ) )
		
		emptyStringPlugPath = fnOH.parameterPlugPath( op["cp"]["emptyString"] )
		self.assertEqual( cmds.getAttr( emptyStringPlugPath ), "notEmpty" )

	def testClassParameterSaveAndLoad( self ) :
	
		# make an opholder with a ClassParameter, and set the held class
		####################################################################
	
		fnOH = IECoreMaya.FnOpHolder.create( "node", "classParameterTest", 1 )

		op = fnOH.getOp()
		fnOH.setClassParameterClass( op["cp"], "maths/multiply", 1, "IECORE_OP_PATHS" )
		
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
										
		# check that maya has appropriate attributes for the held class,
		# and that the held class hasn't changed in the process.
		####################################################################
		
		heldClass2, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		self.failUnless( heldClass is heldClass2 )
				
		# change some parameter values and push them into maya.
		####################################################################
		
		op["cp"]["a"].setNumericValue( 10 )
		op["cp"]["b"].setNumericValue( 20 )
		fnOH.setNodeValues()
			
		self.assertEqual( cmds.getAttr( fnOH.parameterPlugPath( op["cp"]["a"] ) ), 10 )
		self.assertEqual( cmds.getAttr( fnOH.parameterPlugPath( op["cp"]["b"] ) ), 20 )	
		
		# save the scene
		####################################################################
		
		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "classParameter.ma" ) )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )
		cmds.file( new = True, force = True )
		
		# reload it and check we have the expected class and attributes
		####################################################################
		
		cmds.file( scene, open = True )
				
		fnOH = IECoreMaya.FnOpHolder( "node" )

		op = fnOH.getOp()

		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )

		self.assertEqual( cmds.getAttr( fnOH.parameterPlugPath( op["cp"]["a"] ) ), 10 )
		self.assertEqual( cmds.getAttr( fnOH.parameterPlugPath( op["cp"]["b"] ) ), 20 )		
	
	def testClassParameterUndo( self ) :
	
		# make an opholder with a ClassParameter, and check that there is
		# no class loaded
		####################################################################
		
		fnOH = IECoreMaya.FnOpHolder.create( "node", "classParameterTest", 1 )
		op = fnOH.getOp()
		
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass, None )
		self.assertEqual( className, "" )
		self.assertEqual( classVersion, 0 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
	
		# check that undo is enabled
		####################################################################
		
		self.assert_( cmds.undoInfo( query=True, state=True ) )

		# set the class and verify it worked
		####################################################################
		
		fnOH.setClassParameterClass( op["cp"], "maths/multiply", 1, "IECORE_OP_PATHS" )
				
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( heldClass["a"] )
		bPlugPath = fnOH.parameterPlugPath( heldClass["b"] )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 1 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 2 )
		
		# undo and check the class is unset
		#####################################################################
					
		cmds.undo()

		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )

		self.assertEqual( heldClass, None )
		self.assertEqual( className, "" )
		self.assertEqual( classVersion, 0 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		self.failIf( cmds.objExists( aPlugPath ) )
		self.failIf( cmds.objExists( bPlugPath ) )
	
	def testClassParameterUndoWithPreviousValues( self ) :
	
		# make an opholder with a ClassParameter, and check that there is
		# no class loaded
		####################################################################
		
		fnOH = IECoreMaya.FnOpHolder.create( "node", "classParameterTest", 1 )
		op = fnOH.getOp()
		
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass, None )
		self.assertEqual( className, "" )
		self.assertEqual( classVersion, 0 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
	
		# set the class and check it worked
		####################################################################
		
		fnOH.setClassParameterClass( op["cp"], "maths/multiply", 1, "IECORE_OP_PATHS" )
				
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( heldClass["a"] )
		bPlugPath = fnOH.parameterPlugPath( heldClass["b"] )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 1 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 2 )
		
		# change some attribute values
		####################################################################
		
		cmds.setAttr( aPlugPath, 10 )
		cmds.setAttr( bPlugPath, 20 )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 10 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 20 )
		
		# check that undo is enabled
		####################################################################
		
		self.assert_( cmds.undoInfo( query=True, state=True ) )

		# change the class to something else and check it worked
		####################################################################
		
		fnOH.setClassParameterClass( op["cp"], "stringParsing", 1, "IECORE_OP_PATHS" )
				
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "stringParsing" )
		self.assertEqual( className, "stringParsing" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		plugPaths = []
		for p in heldClass.parameters().values() :
		
			plugPath = fnOH.parameterPlugPath( p )
			self.failUnless( cmds.objExists( plugPath ) )
			plugPaths.append( plugPath )
			
		self.failIf( cmds.objExists( aPlugPath ) )
		self.failIf( cmds.objExists( bPlugPath ) )
		
		# undo and check the previous class reappears, along with the
		# previous attribute values
		#####################################################################
					
		cmds.undo()

		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( heldClass["a"] )
		bPlugPath = fnOH.parameterPlugPath( heldClass["b"] )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 10 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 20 )
				
		for p in plugPaths :
		
			self.failIf( cmds.objExists( plugPath ) )
		
	def testClassParameterReferenceEdits( self ) :
	
		# make a file with a class parameter with no held class
		#######################################################################
		
		fnOH = IECoreMaya.FnOpHolder.create( "node", "classParameterTest", 1 )
		op = fnOH.getOp()

		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass, None )
		self.assertEqual( className, "" )
		self.assertEqual( classVersion, 0 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "classParameterReference.ma" ) )
		referenceScene = cmds.file( force = True, type = "mayaAscii", save = True )

		# make a new scene referencing that file
		#######################################################################
	
		cmds.file( new = True, force = True )
		cmds.file( referenceScene, reference = True, namespace = "ns1" )

		# set the held class and change some attribute values
		#######################################################################
		
		fnOH = IECoreMaya.FnOpHolder( "ns1:node" )
		op = fnOH.getOp()
				
		fnOH.setClassParameterClass( op["cp"], "maths/multiply", 1, "IECORE_OP_PATHS" )
				
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( heldClass["a"] )
		bPlugPath = fnOH.parameterPlugPath( heldClass["b"] )
		
		cmds.setAttr( aPlugPath, 10 )
		cmds.setAttr( bPlugPath, 20 )
		
		# save the scene
		#######################################################################
		
		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "classParameterReferencer.ma" ) )
		referencerScene = cmds.file( force = True, type = "mayaAscii", save = True )

		# reload it and check all is well
		#######################################################################

		cmds.file( new = True, force = True )
		cmds.file( referencerScene, force = True, open = True )
	
		fnOH = IECoreMaya.FnOpHolder( "ns1:node" )
		op = fnOH.getOp()
				
		heldClass, className, classVersion, searchPath = op["cp"].getClass( True )
		self.assertEqual( heldClass.typeName(), "multiply" )
		self.assertEqual( className, "maths/multiply" )
		self.assertEqual( classVersion, 1 )
		self.assertEqual( searchPath, "IECORE_OP_PATHS" )
		
		aPlugPath = fnOH.parameterPlugPath( heldClass["a"] )
		bPlugPath = fnOH.parameterPlugPath( heldClass["b"] )
		
		self.assertEqual( cmds.getAttr( aPlugPath ), 10 )
		self.assertEqual( cmds.getAttr( bPlugPath ), 20 )
	
	def testOpHolderImport( self ) :
	
		# make a file with an op holder in it
		#######################################################################
	
		fnOH = IECoreMaya.FnOpHolder.create( "node", "maths/multiply", 2 )
		op = fnOH.getOp()
		
		aPlugPath = fnOH.parameterPlugPath( op["a"] )
		bPlugPath = fnOH.parameterPlugPath( op["b"] )
		
		cmds.file( rename = os.path.join( os.getcwd(), "test", "IECoreMaya", "op.ma" ) )
		scene = cmds.file( force = True, type = "mayaAscii", save = True )
		
		# import it into a new scene
		#######################################################################
		
		cmds.file( new = True, force = True )
		cmds.file( scene, i = True )
		
		cmds.setAttr( aPlugPath, 10 )
		cmds.setAttr( bPlugPath, 12 )

		self.assertEqual( cmds.getAttr( "node.result" ), 120 )
		
	def tearDown( self ) :

		for f in [
			"test/IECoreMaya/op.ma" ,
			"test/IECoreMaya/defaultConnections.ma" ,
			"test/IECoreMaya/compoundObjectConnections.ma" ,
			"test/IECoreMaya/reference.ma" ,
			"test/IECoreMaya/referenceMaster.ma",
			"test/IECoreMaya/classParameterReference.ma" ,
			"test/IECoreMaya/classParameterReferencer.ma" ,
			"test/IECoreMaya/objectParameterIO.ma",
			"test/IECoreMaya/imageProcedural.ma",
			"test/IECoreMaya/classParameter.ma",
		] :

			if os.path.exists( f ) :

				os.remove( f )

if __name__ == "__main__":
	MayaUnitTest.TestProgram()
