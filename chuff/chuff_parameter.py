from collections import OrderedDict


class ChuffParameter(object):
    '''
        Chuff Parameter class.

    '''

    def __init__(self):
        self.params = OrderedDict()
        pass

    @staticmethod
    def read_from_mfile(filename):
        '''
        read parameters from old m file. (Matlab format file). Adapted from
        original Chuff script
        :param str filename: The m file contains the parameters.
        '''
        cp = ChuffParameter()

        pfile = open(filename)

        for line in pfile:
            key, value = parse_m_file_line(line)
            if key is not None and len(key) > 0:
                cp.params[key] = value
        return cp

    def write_to_mfile(self, filename):
        pass

    def __getattr__(self, key):
        return self.params[key]
    def __getitem__(self, key):
        return self.params[key]

    def param_type(self, key):
        return type(self.params[key])

def chuff_parameter_to_str(cp):
    s = []
    for key, value in cp.params.items():
        s.append("%s = %s" % (key, value))
    return "\n".join(s)

def parse_m_file_line(line):
    key = None
    value = None
    line = line.strip()
    if line and not line.startswith("#"):
        p_idx = line.find("#")
        if p_idx > 0:
            line = line[:p_idx]
        line=line.strip().strip(";")
        line = line.split("=")
        key = line[0].strip()
        if len(line) > 1:
            value = line[1].strip()
            # guess value type
            if len(value) == 0:
                value = None
            else:
                try:
                    value = eval(value)
                except:
                    pass

    return key, value
