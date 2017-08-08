from torch import nn
from torch.autograd import Variable
from .random_variables import RandomVariable
from .parameters import ParameterGroup
from .lazy import LazyVariable


class Module(nn.Module):
    def __init__(self):
        super(Module, self).__init__()
        self._parameter_groups = {}

    def forward(self, *inputs, **kwargs):
        raise NotImplementedError

    def __call__(self, *inputs, **kwargs):
        for input in inputs:
            if not(isinstance(input, RandomVariable) or isinstance(input, Variable)):
                raise RuntimeError('Input must be a RandomVariable or Variable, was a %s' %
                                   input.__class__.__name__)
        outputs = self.forward(*inputs, **kwargs)
        if isinstance(outputs, Variable) or isinstance(outputs, RandomVariable) or isinstance(outputs, LazyVariable):
            return outputs

        for output in outputs:
            if not (isinstance(output, RandomVariable) or
                    isinstance(output, Variable) or
                    isinstance(output, LazyVariable)):
                raise RuntimeError('Output must be a RandomVariable, Variable, or LazyVariable. Was a %s' %
                                   input.__class__.__name__)
        if len(outputs) == 1:
            outputs = outputs[0]
        return outputs

    def __setattr__(self, name, value):
        if isinstance(value, nn.Parameter):
            raise RuntimeError('Observation Models expect ParameterGroups, not nn.Parameters directly.')
        if isinstance(value, ParameterGroup):
            self._parameter_groups[name] = value
        super(Module, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == '__setstate__':
            # Avoid issues with recursion when attempting deepcopy
            raise AttributeError
        else:
            for param_name, value in self.named_parameter_groups():
                if name == param_name:
                    return value

        return super(Module, self).__getattr__(name)

    def parameter_groups(self):
        for name, param_group in self.named_parameter_groups():
            yield param_group

    def named_parameter_groups(self):
        for name, param_group in self._parameter_groups.items():
            yield name, param_group

        for child in self.children():
            if isinstance(child, Module):
                for name, param_group in child.named_parameter_groups():
                    yield name, param_group