# ezconfigparser

`ezconfigparser` is a library aims at finding an easy way to manipulate configuration files.

`ezconfigparser` makes the parameter files the **ONLY** things that users need paying attention to, and it avoids redundent effort when some parameters are changed/added/removed.

What it can do:

- create template configure file
- parse configure file
- write configure file
- merge configure file
- parse command line arguments based on configure file

## Install & Upgrade

```shell
pip install ezconfigparser --upgrade
```

## How to Use

### Create Template Config File

Write a template config file to `test.cfg`

```python
from ezconfigparser import Config
Config.get_template('test.cfg')
```

### Edit Configure File
A template config file looks like
```text
[MODEL]
# TYPE: float
# DESC: initial learning rate
learning_rate = 1e-3

# TYPE: int
# DESC: batch size
batch_size = 64

# TYPE: str
# DESC: model storage directory
model_dir = /home/blabla/models/test

# compact mode example
(obj) layer_size = [128, 64, 32]
```

A configure file consists of sections (like `[MODEL]` above).

Each section has some parameters shown in `verbose` style or `compact` style.

Possible types of paramters are
- `str`: string
- `float`: float
- `int`: integer
- `json`: json (handled by json.loads)
- `obj`: python object (handled by ast.literal_eval)

For `verbose` style, the type and the description should be specified **STRICTLY** by `# TYPE:` and `# DESC:` (optional, default type is `str` and default description is empty).

For `compact` style, the type is specified by `(<type>)` at the beginning of the same line of the parameter, and the description is deprecated.

### Parse & Use Configure File

Here is an example for how to create `Config` object by parsing the template files.

Firstly, create two config files as the template config file and the target template file using the method in the last section.

```python
from ezconfigparser import Config
# a preset template file, it defines default value of config
template_dir = 'template.cfg'
# a preset target file, it contains values that should be set
target_dir = 'target.cfg'

# Create a Config object with template config
cfg = Config(template_dir, allow_vague=False)

# Parse values in target config and overwrite the default values
cfg.parse(target_dir)

# Access values by Section.Param
print(cfg.MODEL.learning_rate)

# Access values by shortcut
#    all values are also provided with shortcut.
#    When a parameter's name is unique, cfg.<param> is identical to cfg.<section>.<param>. 
#    When a parameter's name is not unique, it can still be accessed in this way if "allow_vague" is set to true (*recommended*). In this case, it represents the last parameter with the same name in config file. If "allow_vague" is false, then it will raise an error if accessed in this way.
print(cfg.learning_rate)

# Modify values manually (not recommened)
#    values can be modified manually like how they're accessed, and it can not create new paramters.
#    But one key idea of ezconfigparser is to keep config seperate from programs, hard coding of modifying parameters in programs is not recommened.
cfg.MODEL.learning_rate = 2e-3
cfg.learning_rate = 8e-4
```

### Write Config File
It may need to store the configure file for checking in the future.
```python
# it can add some comments in the config by passing "note="
cfg.write('./test.cfg', note='some note')
```

### Merge Config File
It can merge two configures into one.
```python
# cfg_a = ...
# cfg_b = ...

# merge cfg_b into cfg_a.
#     parameters that cfg_b has but cfg_a does not have will be created in cfg_a.
#     overwrite the values if both cfg_a and cfg_b have the same parameter and "overwrite" is true.
cfg_a.merge(cfg_b, overwrite=False)
```

### Parse Command Line Arguments
Sometime, one wants to override the parameters from command line, and `ezconfigparser` also provides a convenient way.

Note:
- If using this functionality, all parameters' name and sections' name **MUST** be unique.
- If a parameter is changed by parsing arguments, it can **NOT** be changed in other ways.

```python
# cfg = ...

# Use the parameters in the configure to parse the arguments.
cfg.parse_args()
```

## Future Work

- Provide constrains on the parameter
- Add test cases