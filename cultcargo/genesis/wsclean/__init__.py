from scabha.cargo import Parameter
from typing import Dict, Any

def img_output(imagetype, desc, path, glob=True, must_exist=False):
    # reamp image type to output filename component
    if imagetype == "restored":
        imagetype = "image"
    implicit = f"{{current.prefix}}{path}-{imagetype}.fits"
    if glob:
        implicit = f"=GLOB({implicit})"
    return Parameter(
        info=f"{imagetype.capitalize()} {desc}",
        dtype="List[File]" if glob else "File",
        mkdir=True,
        implicit=implicit,
        must_exist=must_exist)   


def make_stimela_schema(params: Dict[str, Any], inputs: Dict[str, Parameter], outputs: Dict[str, Parameter]):
    """Augments a schema for stimela based on solver.terms"""

    # predict mode has no outputs
    if params.get('predict'):
        return inputs, outputs

    outputs = outputs.copy()

    # nchan -- if not an integer, assume runtime evaluation and >=2 then
    nchan  = params.get('nchan', 1)
    multichan = params.get('multi.chan', not isinstance(nchan, int) or nchan > 1)
    
    stokes = params.get('pol', "I").upper()
    # multi.stokes can be set explicitly
    multistokes = params.get('multi.stokes', stokes != "I")
    # if explicitly multi-pol, set Stokes list to "IQUV" if it's not explicitly set to something else
    if multistokes and stokes == "I":
        stokes = "IQUV"

    # ntime -- if not an integer, assume runtime evaluation and >=2 then
    ntime  = params.get('intervals-out', 1)
    multitime = params.get('multi.intervals', not isinstance(ntime, int) or ntime > 1)

    for imagetype in "dirty", "restored", "residual", "model":
        if imagetype == "dirty" or params.get('niter', 0) > 0:
            must_exist = True
        else:
            must_exist = False
        for st in stokes:
            # define name/description/filename components for this Stokes 
            if multistokes:
                st_name = f"{st.lower()}."
                st_name1 = f".{st.lower()}"
                st_desc = f"Stokes {st} "
                st_fname = f"-{st}"
            else:
                st_name = st_name1 = st_desc = st_fname = ""
            # now form up outputs
            if multitime:
                if multichan:
                    outputs[f"{imagetype}.{st_name}per-interval.per-band"] = img_output(imagetype,
                        f"{st_desc} images per time interval and band",
                        f"-t[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]{st_fname}", 
                        must_exist=must_exist)
                    outputs[f"{imagetype}.{st_name}per-interval.mfs"] = img_output(imagetype,
                        f"{st_desc} MFS image per time interval",
                        f"-t[0-9][0-9][0-9][0-9]-MFS{st_fname}",
                        must_exist=must_exist)
                else:
                    outputs[f"{imagetype}.{st_name}per-interval"] = img_output(imagetype,
                        f"{st_desc} image per time interval",
                        f"-t[0-9][0-9][0-9][0-9]{st_fname}",
                        must_exist=must_exist)

            else:
                if multichan:
                    outputs[f"{imagetype}.{st_name}per-band"] = img_output(imagetype,
                        f"{st_desc} images per band",
                        f"-[0-9][0-9][0-9][0-9]{st_fname}",
                        must_exist=must_exist)
                    outputs[f"{imagetype}.{st_name}mfs"] = img_output(imagetype,
                        f"{st_desc} MFS image",
                        f"-MFS{st_fname}", glob=False,
                        must_exist=must_exist)
                else:
                    outputs[f"{imagetype}{st_name1}"] = img_output(imagetype,
                        f"{st_desc} image",
                        f"{st_fname}", glob=False,
                        must_exist=must_exist)

    return inputs, outputs
