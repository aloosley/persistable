import yaml
from pathlib import Path


def load_yaml(yamlpath):
    with open(yamlpath, 'r') as stream:
        y = yaml.load(stream)

    return y

def yml2api(yamlpath: Path) -> str:

    parsed_yml = load_yaml(yamlpath)

    objects = (
        f'''
class {object_name}(Persistable):
    """
    {obj["description"]}

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
    {obj_property} : {obj['properties'][obj_property]['type']}
        {obj['properties'][obj_property]['description']}'''
                for obj_property in obj["properties"]
            ] if "properties" in obj else []
        ) +
        f'''
    
    Dependencies
    ------------''' +
        "".join(
            [
                f'''
    {dep}'''
                for dep in obj["dependencies"]
            ] if "dependencies" in obj else ["None"]
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
            {req_param_name} : {obj['required_parameters'][req_param_name]['type']}
                {obj['required_parameters'][req_param_name]['description']}''' + (f'''
                EXAMPLES: {repr(obj['required_parameters'][req_param_name]['examples'])}'''
                if 'examples' in obj['required_parameters'][req_param_name] else '') + (f'''
                OPTIONS: {repr(obj['required_parameters'][req_param_name]['options'])}'''
                if 'options' in obj['required_parameters'][req_param_name] else '')
                for req_param_name in obj["required_parameters"]
            ] if "required_parameters" in obj else ["None"]
        ) +
        f'''
                
            Optional Parameters
            -------------------''' +
        "".join(
            [
                f'''
            {opt_param_name} : {obj['optional_parameters'][opt_param_name]['type']}
                {obj['optional_parameters'][opt_param_name]['description']}
                DEFAULT: {repr(obj['optional_parameters'][opt_param_name].get('default', None))}
                EXAMPLES: {repr(obj['optional_parameters'][opt_param_name].get('examples', None))}'''
                for opt_param_name in obj["optional_parameters"]
            ] if "optional_parameters" in obj else ["None"]
        ) +
        f'''
               
        intermediate_datapath : Path
           The path where intermediate data is persisted / loaded
        verbose : bool
           Verbosity flag - False dumps WARNING level logs, True dumps info level logs.
        """
                
        super().__init__(
            payload_name={repr(obj["name"])},
            params=merge_dicts(
                dict(\n''' +
        ",\n".join(
            [
                f'''
                    {opt_param}={repr(obj['optional_parameters'][opt_param].get('default', None))}'''.strip("\n") for opt_param in obj["optional_parameters"]
            ] if "optional_parameters" in obj else []
        ) +
        f'''
                ),
                params
            ),
            workingdatapath=intermediate_datapath,
            required_params={tuple(req_param for req_param in obj.get("required_parameters", tuple()))},
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
        {obj["properties"][obj_property]["description"]}
        """
    
        raise NotImplementedError("Property not implemented.")
    
                ''' for obj_property in obj["properties"]
            ] if "properties" in obj else []
        ) for object_name, obj in parsed_yml.items()
    )

    return objects