from cultcargo import utils
schema = utils.SimpleCab()
schema.init_from_old_cab("casa-mstransform.json")
schema.save("casa-mstransform.yaml")
