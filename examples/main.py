# -*- coding: utf-8 -*-
"""
# Author: lixiang@firebolt
# Created Time : Sun 24 Jul 2022 12:25:03 AM CST
# File Name: common.py
# Description:
"""

def pprint(what, result):
    print('{}\t: {}, dtype = {}'.format(what,result,type(result).__name__))

def main(Ini):
    fini = './main.ini'
    ini = Ini(fini)
    pprint('ini.context'        , ini.context[:20])
    print('')
    pprint('Inline comment'     , ini.find('InlineComment'))
    pprint('findString'         , ini.findString('String'))
    pprint('findNum'            , ini.findNum('FloatOrNum'))
    pprint('findFloat'          , ini.findFloat('FloatOrNum'))
    pprint('findInt'            , ini.findInt('Int'))
    pprint('findBool'           , ini.findBool('Bool'))
    pprint('findStringVec'      , ini.findStringVec('StringList'))
    pprint('findStringVec'      , ini.findStringVec('StringList2'))
    pprint('findNumVec'         , ini.findNumVec('FloatOrNumList'))
    pprint('findFloatVec'       , ini.findFloatVec('FloatOrNumList'))
    pprint('findIntVec'         , ini.findIntVec('IntList'))
    pprint('findBoolVec'        , ini.findBoolVec('BoolList'))
    pprint('Referenced'         , ini.find('Referenced'))
    pprint('Referenced2'        , ini.findFloatVec('Referenced2'))
    pprint('Referenced3'        , ini.find('Referenced3'))
    pprint('Nested list'        , ini.findStringVec('NestedList'))
    pprint('Current directory'  , ini.findString('CurrentDir'))
    pprint('Shell command'      , ini.findStringVec('ShellCommand1'))
    pprint('Shell Command'      , ini.findFloat('ShellCommand2'))
    pprint('Reference in include file'  , ini.find('RefInFile'))
    pprint('Var from TCL'       , ini.find('VarFromTCL1'))
    pprint('Var not from TCL'   , ini.find('VarFromTCL2'))
    pprint('Var from TCL'       , ini.findStringVec('VarFromTCL3'))
    pprint('Var from TCL'       , ini.findStringVec('VarFromTCL4'))
    pprint('Var from TCL'       , ini.findStringVec('VarFromTCL4'))
    pprint('Var from TCL with header'   , ini.findString('TCL~UseDoubleUnderlinesBeforeHeader'))
    pprint('Existance of \'KeyUndefined\''  , ini.exists('KeyUndefined'))
    pprint('Default value of undefined key'     , ini.get('KeyUndefined','ThisIsDefault'))
    pprint('Existance of \'KeyWithDefault\'', ini.exists('KeyWithDefault'))
    pprint('Default value of defined key'       , ini.get('KeyWithDefault','ThisIsDefault'))
    pprint('none-find'          , ini.find('NoneRecognition'))
    pprint('Key defined under both \'[]\' and non-blank header' , ini.find('UnncessaryHeaderTest~HaveYouGotHeader1'))
    pprint('Replace dt=20220101'   , ini.find('Replace',dt=20220101))
    pprint('Original value without replacement'     , ini.find('Replace'))
    pprint('None-getInt on defined key' , ini.getInt('Int',1))
    pprint('None-getInt on defined key of None'   , ini.getInt('NoneRecognition',1))
    pprint('None-getInt on undefined key '   , ini.getInt('NoneRecognition11',1))

    ini.set('SetField',123)
    pprint('Field newly set'    , ini.find('SetField'))


    
