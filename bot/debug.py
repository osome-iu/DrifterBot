"""For logging bug info into debug file."""
import sys, traceback, time
import functools

def FormatExceptionInfo(sys_exc_info, maxTBlevel=5):
  cla, exc, trbk = sys_exc_info
  excName = cla.__name__
  excTb = traceback.format_exc(maxTBlevel)
  return (excName, exc, excTb)

def HandleException(e, optional=None):
  LogToDebug(functools.reduce(lambda x,y: str(x)+"\n"+str(y), FormatExceptionInfo(e),""))
  if optional:
    LogToDebug(optional)

def LogToDebug(s, filename=None):
  if not filename:
    logFile = open('debug.txt','a+')
  else:
    logFile = open(filename,'a+')
  logFile.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
  logFile.write(s)
  logFile.write('\n--------------------------------\n')
  logFile.close()
