template_txt='# Possible types: str, int, float, json (handled by json.loads), obj (handled by ast.literaleval).\n\
# Every parameter starts with "TYPE", "DESC" for type and description, respectively.\n\
#   Default of "TYPE" is str. The line should STRICTLY start with "# TYPE:"\n\
#   Default of "DESC" is ''. The line should STRICTLY start with "# DESC:"\n\
# Or it can be shown in compact style like the one below.\n\n\
# [<section>] means section. A config should have at least 1 section.\n\
# All parameters\' names can only contains numbers, letters and "_".\n\n\
[MODEL]\n\
# TYPE: float\n\
# DESC: initial learning rate\n\
learning_rate = 1e-3\n\n\
# TYPE: int\n\
# DESC: batch size\n\
batch_size = 64\n\n\
# TYPE: str\n\
# DESC: model storage directory\n\
model_dir = /home/blabla/models/test\n\n\
# compact mode example\n\
(obj) layer_size = [128, 64, 32]\n'