from django.shortcuts import render
from django.http import HttpResponse

import sys, io
from .golfish.golfish import Golfish

def index(request):
    if 'code' in request.POST and 'input' in request.POST:
        code = request.POST['code']
        input_ = request.POST['input']
        debug = ('debug' in request.POST)
        code = code.replace("\r\n", "\n")
        input_ = input_.replace("\r\n", "\n")
        d = {"code": code, "input_": input_, "debug": debug}

    elif 'code' in request.GET and 'input' in request.GET:
        code = request.GET['code']
        input_ = request.GET['input']
        debug = ('debug' in request.GET)
        code = code.replace("\r\n", "\n")
        input_ = input_.replace("\r\n", "\n")
        d = {"code": code, "input_": input_, "debug": debug}

    else:
        d = {}

    if 'submitted' in request.POST:
        d["output"] = ""
        
        try:
            interpreter = Golfish(code, input_, debug, online=True)
            
            out = sys.stdout
            sys.stdout = _ = io.StringIO()
            interpreter.run()
            sys.stdout = out
            
            d["output"] += _.getvalue()

        except Exception as e:
            d["output"] += "\n" + str(e)

    return render(request, 'golfish.html', d)
