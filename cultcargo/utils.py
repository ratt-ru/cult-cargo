from typing import Dict, List, Union, Optional, Callable, Any
from scabha.cargo import Parameter, _UNSET_DEFAULT, EmptyDictDefault, ParameterPolicies
from scabha.basetypes import  File, Directory
from scabha.validate import validate_parameters
from dataclasses import dataclass
from omegaconf import OmegaConf, ListConfig
from pydoc import locate


@dataclass
class OldParameter:
    name: str 
    dtype: str
    info: str
    default: Any = None
    required: bool = False
    choices: List[Any] = None
    io: str = None
    mapping: str = None
    check_io: bool = False
    deprecated: bool = False
    positional: bool = False


@dataclass
class SimpleCab:
    inputs: Dict[str, Any] = EmptyDictDefault()
    outputs: Dict[str, Any] = EmptyDictDefault()
    
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
    
    def init_from_old_cab(self, oldcab_file: File):
        """AI is creating summary for init_from_old_cab

        Args:
            oldcab (File): [description]
        """
        oldcab = OmegaConf.load(oldcab_file)
        
        self.inputs = {}
        self.outputs = {}
        for param in oldcab.parameters:
            dtype = self.__to_new_dtype(param)
            oldparam = OldParameter(**param)
            
            policies = ParameterPolicies(positional=oldparam.positional)
            
            self.inputs[param.name] = Parameter(info=oldparam.info, dtype=dtype, policies=policies,
                                                nom_de_guerre=oldparam.mapping,
                                                must_exist=oldparam.check_io)
            
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

        
        
        
        
        
    
    

    