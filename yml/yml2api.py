import yaml
from pathlib import Path


def load_yaml(yamlpath: Path) -> dict:
    with open(yamlpath, 'r') as stream:
        parsed_yml = yaml.load(stream)

    return parsed_yml


def _parse_inside_List(dep):
    """

    Parameters
    ----------
    dep

    Returns
    -------
    Class, extension, type
    """
    if dep.lower().find("list[") != -1:
        # There is a list:
        inside_List = dep.split("List")[-1].strip("[]")
        return inside_List, "_list", "list"
    else:
        return dep, "", dep


def get_code_from_yml(object_name: str, object: dict, super_object: dict, super_class="Persistable") -> str:

    # Prepping dependency information to the code:
    deps = [dep for dep in object["dependencies"]] if "dependencies" in object else []
    parsed_deps = [_parse_inside_List(dep) for dep in deps]

    init_dep_args = ", ".join(
        [f"{super_object[parsd_dep[0]]['name']}{parsd_dep[1]}: {parsd_dep[2]}" for parsd_dep in parsed_deps]
    ) if len(parsed_deps) else "intermediate_datapath: Path"

    init_dep_doc_string = "".join(
        [
            f'''
        {super_object[parsed_dep[0]]['name']}{parsed_dep[1]} : {parsed_dep[2]}
            {parsed_dep[0]} dependency''' for parsed_dep in parsed_deps
        ]
    ) if len(parsed_deps) else '''
        intermediate_datapath : Path
            The path where intermediate data is persisted / loaded'''

    super_init_dep_args = f"from_persistable=[{', '.join([super_object[parsed_dep[0]]['name']+parsed_dep[1] for parsed_dep in parsed_deps])}]" \
        if len(parsed_deps) else "workingdatapath=intermediate_datapath"

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
            ] if "dependencies" in object else []
        ) +
        f'''
               
    def __init__(params: dict, {init_dep_args}, verbose: bool=True):
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
            ] if "required_parameters" in object else []
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
            ] if "optional_parameters" in object else []
        ) +
        f'''     
        {init_dep_doc_string}
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
            {super_init_dep_args},
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


def recyml2api(parsed_yml: dict, original_parsed_yml: dict, subclass_indicator: str="sub_classes", super_class="Persistable"):

    base = list(parsed_yml.keys())

    for key in base:
        if subclass_indicator in parsed_yml[key]:
            yield from recyml2api(parsed_yml[key][subclass_indicator], original_parsed_yml, super_class=key)

    yield from (
        get_code_from_yml(
            object_name=key, object=parsed_yml[key],
            super_object=original_parsed_yml,
            super_class=super_class
        ) for key in base
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

    yield from recyml2api(parsed_yml, parsed_yml, subclass_indicator)
