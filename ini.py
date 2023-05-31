# -*- coding: utf-8 -*-
"""
Configuration tool for xquant platform.
"""

__all__ = [ 'Ini' ]

#%% Import Part
import os,re,copy,time
import numpy as np
import datetime as dm
import subprocess
from typing import Union,Any

#%% Patterns
pRef = r'\%([^\%\s]+)\%'
pCmd = r'\$\((.+)\)'
pRep = r'\$(\w+)\$'
PATT = { 'include'          : r'^include\s+<(.*ini)>\s*$',
         'empty'            : r'^\s*$',
         'header'           : r'^\[(.*)\]\s*$',
         'scala'            : r'^([\w\.]+)\s*\=\s*([^\[\]]+)\s*$',
         'scala_env'        : r'^([\w\.]+)\s*\|=\s*([^\[\]]+)\s*$',
         'scala_last'       : r'^([\w\.]+)\s*\$=\s*([^\[\]]+)\s*$',
         'vec'              : r'^([\w\.]+)\s*\=\s*\[(.*)\]\s*$',
         'vec_env'          : r'^([\w\.]+)\s*\|=\s*\[(.*)\]\s*$',
         'vec_last'         : r'^([\w\.]+)\s*\$=\s*\[(.*)\]\s*$',
         'vec_start'        : r'^([\w\.]+)\s*\=\s*\[([^\]]*)$',
         'vec_start_env'    : r'^([\w\.]+)\s*\|=\s*\[([^\]]*)$',
         'vec_start_last'   : r'^([\w\.]+)\s*\$=\s*\[([^\]]*)$',
         'vec_mid'          : r'\s*([^<>\[\]]+)\s*$',
         'vec_end'          : r'\s*([^\[]*)\]\s*$',
        }

#%% Class of Ini
class Ini():
    '''
    Configuration tool for xquant platform.
    '''
    def __init__(self,fini:str):
        '''
        Initialize Ini object.

        Parameters
        ----------
        fini : str
            Path of the entrance configuration file.

        Attributes
        -----------------
        context : str
            Full contents of Ini object.
        keys : list
            All of the keys of Ini object.
        '''
        self.fini = fini
        #self.fini = fini.replace('~',os.environ['HOME'])  # Unrecognizable in condor
    # Init global dict
        self._init()
    # Parse
        self._parse_fini()

    def _init(self):
    # Environment variables
        # 在命令行设定环境变量时，用'__'代替'~'
        self.env = {k.upper().replace('__','~'):v for k,v in os.environ.items()}
        self.d = copy.deepcopy(self.env)
    # Absolute path of top-level fini
        abs_path = os.path.abspath(self.fini)
        self.d['PATH_FINI'] = abs_path
    # Current dir of top-level fini
        self.d['CUR_DIR'] = os.path.dirname(abs_path)
    # Today
        today_ = dm.datetime.today().strftime('%Y%m%d')
        self.d['TODAY'] = today_
        self.d['DATE'] = today_

    def _parse_fini(self):
    # 栈
        stack_dir = []
        stack_fini = []
        stack_ptr = []
    # 读取原始文件内容
        self.lines = file2list(self.fini)
        push(self.fini,stack_dir,stack_fini,stack_ptr)
    # 逐行分析
        ptr = 0
        keys2rep = []
        self.header = None
        while ptr < len(self.lines):
            l = self.lines[ptr]
        # 去注释
            l,_,comments = l.partition('#') 
            if not l:
                if comments.startswith(' END include'):
                    pop(stack_dir,stack_fini,stack_ptr)
                ptr += 1
                stack_ptr[-1] += 1
                continue
        # 识别正则表达式
            type_,val = self._parse_pattern_type(l)
        # 如果识别不了，报错
            if type_ is None:
                raise INIFormatError('Cannot parse \'{}\' ( file: {}, line: {} ).'.format(l,stack_fini[-1],stack_ptr[-1]+1))
        # include
            elif type_ == 'include':
                fini = self._true_value(val[0])
            # 读新的 ini
                fini_ = push(fini,stack_dir,stack_fini,stack_ptr)
                if not os.path.exists(fini_):
                    print('Warning: {} does not exists. Check 1st time.'.format(fini_))
                    time.sleep(0.3)
                if os.path.exists(fini_):
                    lines = file2list(fini_)
                # 将新的 ini 插入 self.lines 的 self.ptr 指向的位置，同时指针并不移动
                    lines.insert(len(lines),'# END include <{}>'.format(fini))
                    lines.insert(0,'# START include <{}>'.format(fini))
                    self.lines[ptr:ptr+1] = lines
                else:
                    pop(stack_dir,stack_fini,stack_ptr)
                    print('Warning: {} does not exists. Check 2nd time'.format(fini_))
                ptr += 1
        # 其它情况
            else:
            # empty
                if type_ == 'empty':
                    pass
            # header
                elif type_ == 'header':
                    self.header = val[0].upper()
            # assignment start
                elif type_ in ['scala','scala_env','scala_last','vec','vec_start','vec_env','vec_start_env']:
                # check header
                    if self.header is None:
                        raise INIFormatError('No header defined yet! ( file: {}, line: {} ).'.format(stack_fini[-1],stack_ptr[-1]+1))
                    k,v = val[0]
                    field = self._get_field(k)
                # scala
                    if type_ == 'scala':
                        self.d[field] = rep_blanks(self._true_value(v))
                    elif type_ == 'scala_env':
                        # 先读环境变量，若没有环境变量再读文件中的值
                        if field in self.env:
                            self.d[field] = rep_blanks(self._true_value(self.env[field]))
                        else:
                            self.d[field] = rep_blanks(self._true_value(v))
                    elif type_ == 'scala_last':
                        # 放到最后才做 %xxx% 的替换
                        self.d[field] = rep_blanks(v)
                        keys2rep.append(field)
                    elif type_ == 'vec':
                        self.d[field] = rep_blanks(self._true_value(rep_blanks(v)))
                    elif type_ == 'vec_env':
                        # 先读环境变量，若没有环境变量再读文件中的值
                        if field in self.env:
                            self.d[field] = rep_blanks(self._true_value(rep_blanks(self.env[field])))
                        else:
                            self.d[field] = rep_blanks(self._true_value(rep_blanks(v)))
                    elif type_ == 'vec_last':
                        # 放到最后才做 %xxx% 的替换
                        self.d[field] = rep_blanks(v)
                        keys2rep.append(field)
                    elif type_ == 'vec_start':
                        value_str = rep_blanks(v)
                        ignore_vec = False
                    elif type_ == 'vec_start_env':
                        # 先读环境变量，若没有环境变量再读文件中的值
                        if field in self.env:
                            value_str = rep_blanks(self.env[field])
                            self.d[field] = rep_blanks(self._true_value(value_str))
                            ignore_vec = True
                        else:
                            value_str = rep_blanks(v)
                            ignore_vec = False
                    elif type_ == 'vec_start_last':
                        value_str = rep_blanks(v)
                        ignore_vec = False
                        keys2rep.append(field)
                elif type_ in ['vec_mid','vec_end']:
                    if ignore_vec: 
                        ptr += 1
                        stack_ptr[-1] += 1
                        continue
                    else:
                        if type_ == 'vec_mid':
                            value_str = ' '.join([value_str, rep_blanks(val[0])])
                        elif type_ == 'vec_end':
                            value_str = ' '.join([value_str, rep_blanks(val[0])])
                            self.d[field] = rep_blanks(self._true_value(value_str))
            # move
                ptr += 1
                stack_ptr[-1] += 1
    # replace at last
        if keys2rep:
            for k in keys2rep:
                self.d[k] = self._true_value(self.d[k])
            for k in self.d:
                self.d[k] = self._true_value(self.d[k])
    # context
        self.context = '\n'.join(self.lines)
    # keys
        self.keys = list(self.d.keys())

    def _parse_pattern_type(self,s):
        for key,pat in PATT.items():
            content = re.findall(re.compile(pat),s)
            if content: return key,content
        return None,None

    def _true_value(self,s):
        return self._run_command(self._replace_ref(s))

    def _run_command(self,s):
        comm = parse_pattern(s,pCmd)
        if comm:
            for c in comm:
                s = s.replace('$({})'.format(c),subprocess.getoutput(c))
        return s

    def _replace_ref(self,s):
        ref = parse_pattern(s,pRef)
        if ref:
            for r in ref:
                R = r.upper()
                field = self._get_field(R)
                if field in self.d: # 有在同一header下定义的key就先用它，不然再找[]下定义的同名key
                    v = self.d[field]
                else:
                    v = self.d[R]
                s = s.replace('%{}%'.format(r),v)
        return s

    def _get_field(self,key):
        return '{}{}{}'.format(self.header,'~'*(self.header!=''),key.upper())

    def __repr__(self):
        return self.context

    __str__ = __repr__

#---------------------- For Users ----------------------
    def exists(self,field:str) -> bool:
        '''
        Check if a field exists.

        Parameters
        -------------
        field : str
            Name of the field one is checking for.

            If section of the field is empty, just go with the field per se. 
            Otherwise, use ``~`` bridging the section and the field as input, like ``'section~field'``.

        Returns
        ------------
        val : bool
        '''
        return field.upper() in self.keys

    def set(self,field:str,val:Union[str,int,float,bool,list]):
        '''
        Set a piece of content to the ini object.

        Parameters
        --------------
        field : str
            Name of the field.
        val : str, int, float, bool or list
            Value of the content.
        '''
        self.d[field.upper()] = str(val)
    
# find
    def _find(self,field:str,**kwargs):
        s = self.d[field.upper()]
        s = replace(s,**kwargs)
        return s

    def find(self,field:str,**kwargs):
        '''
        Return string-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : str or None
        '''
        v = self._find(field,**kwargs)
        return None if v.lower()=='none' else v

    findString = find

    def findStringVec(self,field:str,**kwargs):
        '''
        Return list-of-strings-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs* for each element.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : list of strings or None
        '''
        v = self._find(field,**kwargs)
        return None if v.lower()=='none' else [s for s in v.split(' ') if s]

    def findBool(self,field:str,**kwargs):
        '''
        Return boolean-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs*.

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : bool or None
        '''
        v = self._find(field,**kwargs)
        return None if v.lower()=='none' else str2bool(v)
    
    def findBoolVec(self,field:str,**kwargs):
        '''
        Return list-of-booleans-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs* for each element.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : list of bools or None
        '''
        v = self._find(field,**kwargs)
        if v.lower()=='none':
            out = None
        else:
            value = [s for s in v.split(' ') if s]
            out = [str2bool(v) for v in value]
        return out

    def findInt(self,field:str,**kwargs):
        '''
        Return integer-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : int or None
        '''
        v = self._find(field,**kwargs)
        return None if v.lower()=='none' else int(v)
    
    def findIntVec(self,field:str,**kwargs):
        '''
        Return numpy-ndarray-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs* for each element.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : numpy.ndarray or None
        '''
        v = self._find(field,**kwargs)
        if v.lower()=='none':
            out = None
        else:
            value = [s for s in v.split(' ') if s]
            out = np.array([int(float(v)) for v in value])
        return out
        
    def findNum(self,field:str,**kwargs):
        '''
        Return float-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : float or None
        '''
        v = self._find(field,**kwargs)
        return None if v.lower()=='none' else float(v)


    def findNumVec(self,field:str,**kwargs):
        '''
        Return numpy-ndarray-format value of the *field*, and substitue patterns of ``$..$`` with *kwargs* for each element.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : numpy.ndarray or None
        '''
        v = self._find(field,**kwargs)
        if v.lower()=='none':
            out = None
        else:
            value = [s for s in re.split(' |,', v.strip('[').strip(']')) if s]
            out = np.array([float(v) for v in value])
        return out
    
    findFloat = findNum
    findFloatVec = findNumVec
 
# get
    def get(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`find <Ini.find>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : str or None or type of *value*
        '''
        return self.find(field,**kwargs) if self.exists(field) else value
    
    getString = get

    def getStringVec(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findStringVec <Ini.findStringVec>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : list of str or None or type of *value*
        '''
        return self.findStringVec(field,**kwargs) if self.exists(field) else value

    def getBool(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findBool <Ini.findBool>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : bool or None or type of *value*
        '''
        return self.findBool(field,**kwargs) if self.exists(field) else value
    
    def getBoolVec(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findBoolVec <Ini.findBoolVec>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : list of bools or None or type of *value*
        '''
        return self.findBoolVec(field,**kwargs) if self.exists(field) else value

    def getInt(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findInt <Ini.findInt>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : int or None or type of *value*
        '''
        return self.findInt(field,**kwargs) if self.exists(field) else value
    
    def getIntVec(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findIntVec <Ini.findIntVec>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : numpy.ndarray or None
        '''
        return self.findIntVec(field,**kwargs) if self.exists(field) else None if value is None else np.array(value).astype(int)
        
    def getNum(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findNum <Ini.findNum>`; else, return float format of *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : float or None or type of *value*
        '''
        return self.findNum(field,**kwargs) if self.exists(field) else value

    def getNumVec(self,field:str,value:Any=None,**kwargs):
        '''
        If *field* exists, equivalent to :py:meth:`findNumVec <Ini.findNumVec>`; else, return *value*.

        If the original value of the field in lower-case equals 'none', then return ``None``

        Parameters
        -------------
        field : str
            Name of the field.
        value : any type, optional (default=None)
            Value to return if *field* deos not exists.
        **kwargs 
            Key-value pairs for substitution.

        Returns
        ----------------
        val : numpy.ndarray or None
        '''
        return self.findNumVec(field,**kwargs) if self.exists(field) else None if value is None else np.array(value).astype(float)
    
    getFloat = getNum
    getFloatVec = getNumVec


 #%% Self-defined Exceptions
    
class INIFormatError(Exception):
    pass

#%% Functions
def file2list(file_):
    with open(file_,'r') as f:
        lines = [l.strip('\n') for l in f.readlines()]
    return lines

parse_pattern = lambda s,pattern: re.findall(re.compile(pattern),s)

def push(fini,stack_dir,stack_fini,stack_ptr):
    if stack_dir:
        fini = os.path.join(stack_dir[-1],fini)
    else:
        fini = os.path.abspath(fini)
    stack_dir.append(os.path.dirname(os.path.abspath(fini)))
    stack_fini.append(fini)
    stack_ptr.append(0)
    return fini

def pop(stack_dir,stack_fini,stack_ptr):
    stack_dir.pop()
    stack_fini.pop()
    stack_ptr.pop()

def rep_blanks(s):
    return re.sub('\s+',' ',s).strip(' ')

def replace(s,**kwargs):
    for k,v in kwargs.items():
        if v is not None:
            s = s.replace('${}$'.format(k),str(v))
    return s

def str2bool(s):
    s = s.lower()
    if s in ['true','t','1']:
        return True
    elif s in ['false','f','0']:
        return False
    else:
        raise Exception('Can\'t convert [{}] to a boolean value.'.format(s))

