from __future__ import print_function
import sys
import json
import time
import logging
import argparse
from ast import literal_eval

logging.basicConfig(format='[%(levelname)s] %(message)s')

if sys.version_info < (3, 0):
    from template import template_txt
else:
    from .template import template_txt

class ParameterSection(object):
    LEGAL_TYPES = ['str', 'int', 'float', 'json', 'obj']

    def __init__(self, section_name):
        self._section_name = section_name
        self._params = {}
        self._keys = []
    
    def add_param(self, _key, _type, _desc, _value, add_new_param=False):
        assert not _key.startswith('_'), 'parameter name can not start with "_"'
        assert (_key in self._params) or add_new_param, 'unexpected key in template, {}'.format(_key)
        assert _type in ParameterSection.LEGAL_TYPES, 'invalid parameter type of key "{}", {}'.format(_key, _type)
        if (_key in self._params) and (self._params[_key]['final']):
            return
        value = None
        if _type == 'int':
            value = int(_value)
        elif _type == 'str':
            value = _value
        elif _type == 'float':
            value = float(_value)
        elif _type == 'json':
            value = json.loads(_value)
        else:
            value = literal_eval(_value)
        self._params[_key] = {
            'type': _type,
            'desc': _desc,
            'final': False,
            'value': value
        }
        self._keys = list(self._params.keys())
    
    def parse_args(self, args):
        for key in self._params:
            try:
                _value = args.__getattribute__(key)
            except:
                continue
            if not (_value is None):
                if self._params[key]['type'] in ['str', 'float', 'int']:
                    self._params[key]['value'] = _value
                elif self._params[key]['type'] == 'json':
                    self._params[key]['value'] = json.loads(_value)
                else:
                    self._params[key]['value'] = literal_eval(_value)
                self._params[key]['final'] = True

    def get_info(self, key):
        _value = self._get_string_value(key)
        return self._params[key]['type'], self._params[key]['desc'], _value
    
    def _get_string_value(self, key):
        if self._params[key] == 'json':
            _value = json.dumps(self._params[key]['value'])
        else:
            _value = self._params[key]['value'].__str__()
        return _value

    def write(self, f, compact=False):
        print('[{}]'.format(self._section_name), file=f)
        for key in self._params:
            _value = self._params[key]['value'].__str__()
            if self._params[key]['type'] == 'json':
                _value = json.dumps(self._params[key]['value'])
            if compact:
                print('({}) {} = {}'.format(self._params[key]['type'], key, _value), file=f)
            else:
                print('# TYPE: {}'.format(self._params[key]['type']), file=f)
                print('# DESC: {}'.format(self._params[key]['desc']), file=f)
                print('{} = {}\n'.format(key, _value), file=f)
        print('', file=f)
    
    def add_arguments(self, parser, disabled_opt):
        for key in self._params:
            if self._params[key]['type'] == 'float':
                _type = float
            if self._params[key]['type'] == 'int':
                _type = int
            else:
                _type = str
            if disabled_opt[key]:
                parser.add_argument('--{}'.format(key), type=_type, help=self._params[key]['desc'], metavar=self._params[key]['type'].upper())
    
    def __getitem__(self, key):
        return self._params[key]['value']

    def __getattr__(self, key):
        return self._params[key]['value']
    
    def __setattr__(self, key, value):
        if key.startswith('_'):
            super(ParameterSection, self).__setattr__(key, value)
        else:
            assert key in self._params, 'Unexpected Key, {}'.format(key)
            if self._params[key]['type'] == 'str':
                assert type(value) == str, 'Unexpect Value Type, {}. Expect str'.format(type(value))
                self._params[key]['value'] = value
            elif self._params[key]['type'] == 'int':
                assert type(value) == int, 'Unexpect Value Type, {}. Expect str'.format(type(value))
                self._params[key]['value'] = value
            elif self._params[key]['type'] == 'float':
                try:
                    value = float(value)
                except:
                    raise ValueError('Invalid Value, {}, for type float'.format(value))
                self._params[key]['value'] = value
            elif self._params[key]['type'] in ['obj', 'json']:
                self._params[key]['value'] = value

    def __iter__(self):
        self._index = 0
        return self
    
    def __next__(self):
        if self._index < len(self._keys):
            key = self._keys[self._index]
            self._index += 1
            return key
        else:
            raise StopIteration
    
    def next(self):
        if self._index < len(self._keys):
            key = self._keys[self._index]
            self._index += 1
            return key
        else:
            raise StopIteration

class VagueValue():
    def __init__(self):
        pass

class Config(object):
    LEGAL_LETTERS = [chr(65 + i) for i in range(26)] + [chr(97 + i) for i in range(26)] + [chr(48 + i) for i in range(10)] + ['_']
    NAME_ERROR_PROMPT = "the name should only contain letters (both upper's and lower's), underline '_', and digits"

    def __init__(self, default_cfg=None, allow_vague=False):
        self._sections = {}
        self._direct_attr = {}
        self._note = ''
        self._allow_vague = allow_vague
        self._loaded = False
        if default_cfg:
            self.parse(default_cfg, True)
    
    def parse(self, cfg_dir, add_new_param=False):
        add_new_param = add_new_param or (not self._loaded)
        section_name = None
        param_type = 'str'
        param_desc = ''
        _section_keys = set()
        _param_keys = set()
        with open(cfg_dir, 'r') as f:
            line = f.readline()
            while line:
                line = line.strip(' \n\r\t')
                if line.startswith('['):
                    section_name = line.strip('[] ')
                    assert len(section_name), 'empty section name'
                    assert not section_name.startswith('_'), 'section name can not start with "_"'
                    assert not section_name[0].isdigit(), 'section name can not start with digits'
                    assert not any([not (x in Config.LEGAL_LETTERS) for x in section_name]), 'invalid section name, {}\n{}'.format(section_name, self.NAME_ERROR_PROMPT)
                    assert not (section_name in _section_keys), 'repeated decleration of section, {}'.format(section_name)
                    if not (section_name in self._sections):
                        self._sections[section_name] = ParameterSection(section_name)
                    _section_keys.add(section_name)
                    _param_keys = set()
                elif line.startswith('('):  # Compact Mode Parameter
                    param_type = line[:line.index(')')].strip('() ')
                    param_desc = ''
                    line = line[line.index(')') + 1:]
                    param_name = line.split('=')[0].strip(' ')
                    param_value = line[line.index('=') + 1:].strip(' ')
                    assert section_name, 'no section specified above'
                    assert len(param_name), 'empty parameter name'
                    assert not param_name.startswith('_'), 'parameter name can not start with "_"'
                    assert not param_name[0].isdigit(), 'parameter name can not start with digits'
                    assert not any([not (x in Config.LEGAL_LETTERS) for x in param_name]), 'invalid parameter name, {}\n{}'.format(section_name, self.NAME_ERROR_PROMPT)
                    if param_name in _param_keys:
                        logging.warn('Parameter "{}" appears multiple times in config "{}"'.format(param_name, cfg_dir))
                    self._sections[section_name].add_param(param_name, param_type, param_desc, param_value, add_new_param=add_new_param)
                    _param_keys.add(param_name)
                    param_type = 'str'
                    param_desc = ''
                elif line.startswith('# TYPE:'):  # Verbose Mode Parameter Type
                    param_type = line[7:].strip(' ')
                elif line.startswith('# DESC:'):  # Verbose Mode Parameter Type
                    param_desc = line[7:].strip(' ')
                elif not line.startswith('#'):  # Might be Verbose Mode Parameter
                    if '=' in line:
                        param_name = line.split('=')[0].strip(' ')
                        param_value = line[line.index('=') + 1:].strip(' ')
                        assert section_name, 'no section specified above'
                        assert len(param_name), 'empty parameter name'
                        assert not param_name.startswith('_'), 'parameter name can not start with "_"'
                        assert not param_name[0].isdigit(), 'parameter name can not start with digits'
                        assert not any([not (x in Config.LEGAL_LETTERS) for x in param_name]), 'invalid parameter name, {}\n{}'.format(section_name, self.NAME_ERROR_PROMPT)
                        if param_name in _param_keys:
                            logging.warn('Parameter "{}" appears multiple times'.format(param_name))
                        self._sections[section_name].add_param(param_name, param_type, param_desc, param_value, add_new_param=add_new_param)
                        _param_keys.add(param_name)
                        param_type = 'str'
                        param_desc = ''
                elif line.startswith('# NOTE:'):
                    self._note = line[7:].strip(' ')
                else:
                    pass
                line = f.readline()
        self._loaded = True
        self._build_direct_attr()

    def write(self, cfg_dir, note=None, compact=False):
        with open(cfg_dir, 'w') as f:
            print('# NOTE: {}'.format(note if note else self._note), file=f)
            print('# TIMESTAMP: {}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S")), file=f)
            for section in self._sections:
                self._sections[section].write(f, compact=compact)
    
    def get_parser(self):
        parser = argparse.ArgumentParser(description=self._note)
        parser.add_argument('-c', '--config', type=str, help='config file directory')
        disabled_opt = {'config': False}
        for section in self._sections:
            for param in self._sections[section]:
                if param in disabled_opt:
                    disabled_opt[param] = False
                else:
                    disabled_opt[param] = True
        for section in self._sections:
            group = parser.add_argument_group(title=section)
            self._sections[section].add_arguments(group, disabled_opt)
        return parser
    
    def parse_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        for section in self._sections:
            self._sections[section].parse_args(args)
        self._build_direct_attr()
        if args.config:
            self.parse(args.config)
    
    def merge(self, other, overwrite=False):
        for section in other._sections:
            if not (section in self._sections):
                self._sections[section] = ParameterSection(section)
            for param in other._sections[section]:
                _type, _desc, _value = other._sections[section].get_info(param)
                if (not (param in self._sections[section])) or overwrite:
                    self._sections[section].add_param(param, _type, _desc, _value, add_new_param=True)
        self._build_direct_attr()

    def _build_direct_attr(self):
        self._direct_attr = {}
        for section in self._sections:
            self._direct_attr[section] = self._sections[section]
        for section in self._sections:
            for param in self._sections[section]:
                if not (param in self._direct_attr):
                    self._direct_attr[param] = (section, param)
                else:
                    if not self._allow_vague:
                        self._direct_attr[param] = VagueValue()

    def __getattr__(self, key):
        if key in self._direct_attr:
            assert not isinstance(self._direct_attr[key], VagueValue), 'Can not use vague param, {}'.format(key)
            if isinstance(self._direct_attr[key], tuple):
                return self._sections[self._direct_attr[key][0]].__getattr__(self._direct_attr[key][1])
            else:
                return self._direct_attr[key]
        else:
            raise AttributeError('Unexpect Attribute, {}'.format(key))
    
    def __setattr__(self, key, value):
        if key.startswith('_'):  # Internal Variables
            super(Config, self).__setattr__(key, value)
        else:  # Trying to Set Some Parameters
            if not (key in self._direct_attr):
                raise AttributeError('Setting Unexpect Attribute, {}'.format(key))
            else:
                if isinstance(self._direct_attr[key], VagueValue) and (not self._allow_vague):
                    raise AttributeError('Can not set vague param, {}'.format(key))
                if isinstance(self._direct_attr[key], ParameterSection):
                    raise AttributeError('Can not set values to section, {}'.format(key))
                
                section = self._direct_attr[key][0]
                self._sections[section].__setattr__(key, value)

    @staticmethod
    def get_template(template_dir):
        with open(template_dir, 'w') as f:
            print(template_txt, file=f)

if __name__ == '__main__':
    x = Config('./ezconfigparser/test/data.cfg')
    x.parse('./ezconfigparser/test/data_a.cfg')

    y = Config('./ezconfigparser/test/model.cfg')
    y.parse('./ezconfigparser/test/model_a.cfg')

    x.merge(y)
    x.write('test.cfg', 'haha')
