from typing import Dict, List, Union, Optional, Callable, Any
from scabha.cargo import Parameter, _UNSET_DEFAULT, EmptyListDefault
from scabha.cargo import EmptyDictDefault, ParameterPolicies, Cargo
from scabha.basetypes import  File, Directory
from scabha.validate import validate_parameters
from dataclasses import dataclass
from omegaconf import OmegaConf, ListConfig
from pydoc import locate


@dataclass
class OldParameter:
    name: str 
    dtype: Any
    info: str
    default: Any = None
    required: bool = False
    choices: Optional[List[Any]] = None
    io: Optional[str] = ""
    mapping: Optional[str] = ""
    check_io: bool = False
    deprecated: bool = False
    positional: bool = False


@dataclass
class OldCab:
    task: str
    base: str
    version: List[str]
    binary: str = ""
    description: str = "<documentation>"
    prefix: str = "--"
    parameters: Optional[List[Dict]] = None
    tag: Optional[List[str]] = None
    junk: Optional[List[str]] = None
    msdir: bool = False
    wranglers: Optional[List[str]] = None

class SimpleCab:
    def __init__(self, oldfile: File):
        self.oldfile = oldfile
        cab_strct = OmegaConf.structured(OldCab)
        param_strct = OmegaConf.structured(OldParameter)
        _oldcab = OmegaConf.load(oldfile)
        self.oldcab = OmegaConf.merge(cab_strct,
                                    OmegaConf.load(oldfile))
        self.parameters = []
        for param in _oldcab.parameters:
            pardict = OmegaConf.merge(param_strct, param)
            self.parameters.append(pardict)
            
        
    
    def __to_new_dtype(self, param:OldParameter) -> str:
        new_dtype = []
        if isinstance(param.dtype, (list, ListConfig)):
            islist = True
            dtype = param.dtype
        else:
            islist = False
            dtype = [param.dtype]
            
        for item in dtype:
            listof = False
            if item.startswith("list:"):
                item = item.split(":")[-1] 
                listof = True
    
            if item == "file":
                if param.get("io", "") == "msfile":
                    newtype = "MS"
                else:
                    newtype = "File"
            else:
                newtype = item
            
            if listof:
                new_dtype.append(f"List[{newtype}]")
            else:
                new_dtype.append(newtype)
        if islist:
            return "Union[" + ",".join(new_dtype) + "]"
        else:
            return new_dtype[0]
        
    
    def to_new_params(self, set_inputs=True):
        """AI is creating summary for init_from_old_cab

        Args:
            oldcab (File): [description]
        """
        param_struct = OmegaConf.structured(Parameter)
        params = {}
        for param in self.parameters:
            dtype = self.__to_new_dtype(param)
            
            policies = ParameterPolicies(positional=param.positional)
            
            params[param.name] = OmegaConf.merge(param_struct,
                            dict(info=param.info, dtype=dtype, policies=policies,
                                nom_de_guerre=param.mapping,
                                must_exist=param.check_io))
            if set_inputs:
                self.inputs = params
                self.outputs = {}
        return OmegaConf.create(params)
    
    
    def save(self, path: str):
        """_summary_

        Args:
            path (str): _description_

        Returns:
            _type_: _description_
        """
        
        outdict = OmegaConf.create({"inputs": self.inputs,
                                    "outputs": self.outputs,
                                    })
        OmegaConf.save(outdict, path)
        
        return 0

        
        
        
        
        
    
    

    