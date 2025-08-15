import operator
import string

"""
This implementation is taken directly from https://codereview.stackexchange.com/questions/46698/small-python-calculator by user Sean Perry (github: github.com/shaleh, user_profile: https://codereview.stackexchange.com/users/35547/sean-perry)
"""

class EvaluationError(Exception):


    def __str__(self):
        return "The expression could not be evaluated."


class InvalidNumber(Exception):

    def __str__(self):
        return "The expression has invalid numbers."


class InvalidOperator(Exception):

    def __str__(self):
        return "The expression has invalid operators. The valid operators are +, -, *, /, and ^."


class UnbalancedParens(Exception):

    def __str__(self):
        return "The expression has unbalanced parentheses."


def cast(value):
    """Attempt to turn a value into a number."""
    if isinstance(value, (int, float)):
        return value

    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass

    raise InvalidNumber(value)


class Operator(object):
    def __init__(self, op, precedence):
        self._op = op
        self._prec = precedence

    def __call__(self, *args):
        return self._op(*args)

    def __lt__(self, op):
        return self._prec < op._prec

    def __gt__(self, op):
        return self._prec > op._prec

    def __eq__(self, op):
        return self._prec == op._prec

    def __repr__(self):
        return repr(self._op)

    def __str__(self):
        return str(self._op)


class Calculator(object):
    operators = {
        "+": Operator(operator.add, 1),
        "-": Operator(operator.sub, 1),
        "*": Operator(operator.mul, 2),
        "/": Operator(operator.truediv, 2),
        "^": Operator(operator.pow, 3),
    }

    def __init__(self):
        pass

    def calculate(self, expr):
        """Parse and evaluate the expression."""
        tokens = self.parse(expr)
        result = self.evaluate(tokens)
        return round(result, 5)

    def evaluate(self, tokens, trace=False):
        """Walk the list of tokens and evaluate the result."""
        stack = []
        for item in tokens:
            if isinstance(item, Operator):
                if trace:
                    print(stack)

                if len(stack) == 1 and item == self.operators["-"]:
                    stack.append(-cast(stack.pop()))
                else:
                    b, a = cast(stack.pop()), cast(stack.pop())
                    result = item(a, b)
                    stack.append(result)

                if trace:
                    print(stack)
            else:  # anything else just goes on the stack
                if item.endswith("."):
                    raise InvalidNumber(item)
                stack.append(item)

        if len(stack) > 1:
            raise EvaluationError(str(stack))

        return stack[0]

    def parse(self, expr, trace=False):
        """Take an infix arithmetic expression and return the expression parsed into postfix notation.
        Note the numbers are left as strings to be evaluated later.
        """
        tokens = []
        op_stack = []

        last = None
        i = 0
        while i < len(expr): 
            c = expr[i]
            if c in string.whitespace:
                last = c
            elif c in string.digits:
                value = str(c)
                if last and last in string.digits:  # number continues, just append it
                    value = tokens.pop() + value

                last = c
                tokens.append(value)
            elif c == ".":
                if last and last in string.digits:  # looks like a decimal
                    tokens.append(tokens.pop() + ".")
                else:
                    raise InvalidNumber("misplaced decimal")
            elif c == "(":                
                # take into account unary minus
                next_closed = expr.find(")", i)
                if next_closed == -1:
                    raise UnbalancedParens()
                if i == next_closed - 1:
                    raise InvalidNumber("missing number")
                inside = expr[i + 1:next_closed]
                if not inside.strip():
                    raise InvalidNumber("missing number")

                stripped_inside = inside.strip()
                if stripped_inside[0] == "-" and stripped_inside[1:].strip().isdigit():
                    tokens.append(f"-{stripped_inside[1:].strip()}")
                    i = next_closed
                else:
                    op_stack.append("(")

            elif c == ")":
                if not op_stack:
                    raise UnbalancedParens(c)

                # closing parens found, unwind back to the matching open
                while op_stack:
                    curr = op_stack.pop()
                    if curr is "(":
                        break
                    else:
                        tokens.append(curr)
            else:  # not a number or a parens, must be an operator
                op = self.operators.get(c, None)
                if op is None:
                    raise InvalidOperator(c)

                while op_stack:
                    curr = op_stack[-1]
                    # the 'is' check prevents comparing an Operator to a string
                    if curr is "(":  # don't leave the current scope
                        break
                    elif curr < op:
                        break
                    tokens.append(op_stack.pop())

                op_stack.append(op)
                last = c

            if trace:
                print("----")
                print(tokens)
                print(op_stack)
                print("----")

            i += 1

        while op_stack:
            op = op_stack.pop()
            if op is "(":
                raise UnbalancedParens()
            tokens.append(op)

            if trace:
                print("----")
                print(tokens)
                print(op_stack)
                print("----")

        return tokens
