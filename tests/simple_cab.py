from cultcargo import utils
from scabha.basetypes import File
import os.path
testdir = os.path.dirname(os.path.abspath(__file__))

oldcab = File(f"{testdir}/casa-mstransform.json")
newcab = f"{oldcab.BASENAME}.yaml"
schema = utils.SimpleCab(oldcab)
schema.to_new_params()
schema.save(newcab)

