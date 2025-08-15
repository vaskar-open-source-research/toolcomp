from abc import abstractmethod
import json

class ToolBaseClass:

    def __init__(self):
        pass

    @abstractmethod
    def validate(self, args):
        pass

    @abstractmethod
    def call(self, args):
        """
        args: a dictionary of arguments
        """
        pass

    @abstractmethod
    def get_description(self):
        pass
    
    def get_gpt_spec(self, type="function"):

        desc=self.get_firefunction_spec()
        gpt_desc={}
        gpt_desc['type']=type
        gpt_desc['function']=desc

        return gpt_desc
    
    def parse_and_hit_tool(self, args, historical_date=None):
        if isinstance(args, str):
            try:
                try:
                    args=json.loads(args)
                except:
                    args=json.loads(args.replace('\\\\', '\\').replace("\n", "\\n"))
                if 'fields' in args:
                    d=args['fields']
                    while 'struct_value' in d['value']:
                        d=d['value']['struct_value']
                    args[d['key']]=d['value']['string_value']
                if 'code' in args:
                    args['code']=args['code'].replace('\\n','\n')
                args={k: v.replace('\\n', '\n') if isinstance(v, str) else v for k, v in args.items()}
            except:
                return json.dumps({"error": "Invalid input. Please provide a valid JSON object."})
        else:
            if 'code' in args:
                args['code']=args['code'].replace('\\n','\n').replace('\\', '')
        args['historical_date'] = historical_date
        return json.dumps(self.call(args))
