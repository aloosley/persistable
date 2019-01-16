import yaml
from pathlib import Path


def load_yaml(yamlpath: Path) -> dict:
    with open(yamlpath, 'r') as stream:
        parsed_yml = yaml.load(stream)

    return parsed_yml

def get_code_from_yml(object_name: str, object: dict, super_class="Persistable") -> str:
    return (
        f'''
class {object_name}({super_class}):
    """
    {object["description"]}

    Payload
    -------
    payload     : recdefaultdict
    |-- [key1]      : [type1]
    |   Description for [key1]
    |-- [key2]      : [type2]
    |   Description for [key1]
    |   |-- [key2.1] : [type2.1]
    |   |   Description for [key1]

    Properties
    ----------''' +
        "".join(
            [
                f'''
    {obj_property} : {object['properties'][obj_property]['type']}
        {object['properties'][obj_property]['description']}'''
                for obj_property in object["properties"]
            ] if "properties" in object else []
        ) +
        f'''
    
    Dependencies
    ------------''' +
        "".join(
            [
                f'''
    {dep}'''
                for dep in object["dependencies"]
            ] if "dependencies" in object else ["None"]
        ) +
        f'''
               
    def __init__(params: dict, intermediate_datapath: Path, verbose: bool=True):
        """
        Initiate persistable object.
        
        Parameters
        ----------
        params : dict
        
            Required Parameters
            -------------------''' +
        "".join(
            [
                f'''
            {req_param_name} : {object['required_parameters'][req_param_name]['type']}
                {object['required_parameters'][req_param_name]['description']}''' + (f'''
                EXAMPLES: {repr(object['required_parameters'][req_param_name]['examples'])}'''
                if 'examples' in object['required_parameters'][req_param_name] else '') + (f'''
                OPTIONS: {repr(object['required_parameters'][req_param_name]['options'])}'''
                if 'options' in object['required_parameters'][req_param_name] else '')
                for req_param_name in object["required_parameters"]
            ] if "required_parameters" in object else ["None"]
        ) +
        f'''
                
            Optional Parameters
            -------------------''' +
        "".join(
            [
                f'''
            {opt_param_name} : {object['optional_parameters'][opt_param_name]['type']}
                {object['optional_parameters'][opt_param_name]['description']}
                DEFAULT: {repr(object['optional_parameters'][opt_param_name].get('default', None))}
                EXAMPLES: {repr(object['optional_parameters'][opt_param_name].get('examples', None))}'''
                for opt_param_name in object["optional_parameters"]
            ] if "optional_parameters" in object else ["None"]
        ) +
        f'''
               
        intermediate_datapath : Path
           The path where intermediate data is persisted / loaded
        verbose : bool
           Verbosity flag - False dumps WARNING level logs, True dumps info level logs.
        """
                
        super().__init__(
            payload_name={repr(object["name"])},
            params=merge_dicts(
                dict(\n''' +
        ",\n".join(
            [
                f'''
                    {opt_param}={repr(object['optional_parameters'][opt_param].get('default', None))}'''.strip("\n") for opt_param in object["optional_parameters"]
            ] if "optional_parameters" in object else []
        ) +
        f'''
                ),
                params
            ),
            workingdatapath=intermediate_datapath,
            required_params={tuple(req_param for req_param in object.get("required_parameters", tuple()))},
            excluded_fn_params=[],
            verbose=verbose
        )
        
    def _generate_payload(self, **untracked_payload_params):
        """
        Function that defines how payload is generated.
        
        Parameters
        ----------
        untracked_payload_params    : dict
        """
        
        raise NotImplementedError("_generate_payload() not implemented.")
               
        ''' + "\n".join(
            [
                f'''
    @property
    def {obj_property}(self):
        """
        {object["properties"][obj_property]["description"]}
        """
    
        raise NotImplementedError("Property not implemented.")
    
                ''' for obj_property in object["properties"]
            ] if "properties" in object else []
        )
    )


def recyml2api(parsed_yml: dict, subclass_indicator: str="sub_classes", super_class="Persistable"):

    base = list(parsed_yml.keys())

    for key in base:
        if subclass_indicator in parsed_yml[key]:
            yield from recyml2api(parsed_yml[key][subclass_indicator], super_class=key)

    yield from (
        get_code_from_yml(key, parsed_yml[key], super_class=super_class) for key in base
    )


def yml2api(yamlpath: Path, subclass_indicator: str="sub_classes"):
    """
    Given a subclass indicator, this function recursively writes persistable class code for all persistable classes.

    Parameters
    ----------
    yamlpath            : Path
        Location of persistable api schema
    subclass_indicator  : str
        Syntax for subclasses

    Returns
    -------

    """

    parsed_yml = load_yaml(yamlpath)

    yield from recyml2api(parsed_yml, subclass_indicator)
