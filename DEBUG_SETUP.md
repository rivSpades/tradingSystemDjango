# Django Debugging Setup Guide

This guide will help you set up debugging for your Django trading system project.

## 🚀 Quick Start (Recommended)

### Option 1: Install Enhanced Debugger (ipdb)

```bash
# Install ipdb for better debugging experience
pip install ipdb

# Or install all debugging tools
pip install -r requirements_debug.txt
```

### Option 2: Use Built-in Python Debugger (pdb)

No installation needed - pdb is built into Python!

## 🐛 How to Use the Debugger

### Method 1: Using the Debug Scripts

#### Basic Debugging:
```bash
# Run the basic debug script
python debug_example.py
```

#### Enhanced Debugging:
```bash
# Run the enhanced debug script with ipdb
python debug_backtest_enhanced.py
```

#### Quick Debug Helpers:
```bash
# Run quick debug helpers
python debug_helpers.py
```

### Method 2: Using VS Code Debugger

1. **Open VS Code** in your project directory
2. **Go to Debug panel** (Ctrl+Shift+D)
3. **Select a debug configuration**:
   - "Django Debug" - Debug Django server
   - "Django Shell Debug" - Debug Django shell
   - "Debug Backtest Script" - Debug your scripts
   - "Debug Management Command" - Debug management commands
4. **Set breakpoints** by clicking in the left margin of your code
5. **Press F5** to start debugging

### Method 3: Using Django Shell

```bash
# Start Django shell with debugger
python manage.py shell

# In the shell:
>>> from debug_helpers import debug_66
>>> debug_66()  # This will start debugging backtest 66
```

### Method 4: Adding Breakpoints to Your Code

Add this line anywhere in your code where you want to stop:

```python
# For basic debugging
import pdb; pdb.set_trace()

# For enhanced debugging (if ipdb is installed)
import ipdb; ipdb.set_trace()

# Or use the helper function
from debug_helpers import debug_break
debug_break()
```

## 🎯 Debug Commands

When the debugger stops, you can use these commands:

### Basic Commands:
- `n` (next) - Execute the next line
- `s` (step) - Step into a function
- `c` (continue) - Continue execution
- `q` (quit) - Quit the debugger
- `l` (list) - Show current code
- `p variable_name` - Print a variable
- `pp variable_name` - Pretty print a variable

### Advanced Commands:
- `w` (where) - Show call stack
- `u` (up) - Move up in call stack
- `d` (down) - Move down in call stack
- `h` (help) - Show help
- `!command` - Execute Python command

## 🔍 Specific Debugging Scenarios

### Debug Backtest 66:
```python
from debug_helpers import debug_66
debug_66()
```

### Debug Portfolio Analysis:
```python
from debug_helpers import debug_portfolio_66
debug_portfolio_66()
```

### Debug Strategy Calculation:
```python
from debug_helpers import debug_calc_66
debug_calc_66()
```

### Debug Any Backtest:
```python
from debug_helpers import inspect_backtest
inspect_backtest(67)  # Replace with your backtest ID
```

## 🛠️ VS Code Setup

1. **Install Python extension** in VS Code
2. **Open your project** in VS Code
3. **The launch.json file** is already configured
4. **Set breakpoints** by clicking in the left margin
5. **Press F5** to start debugging

## 📊 Django Debug Toolbar (Optional)

For web-based debugging:

1. **Install Django Debug Toolbar**:
```bash
pip install django-debug-toolbar
```

2. **Add to your settings.py**:
```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

3. **Add to your urls.py**:
```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
```

## 🎯 Debugging Your Specific Issue

To debug the "No active strategy symbols" issue:

1. **Run the enhanced debug script**:
```bash
python debug_backtest_enhanced.py
```

2. **Or use the quick helper**:
```python
from debug_helpers import debug_66
debug_66()
```

3. **Step through the code** to see:
   - What trades exist
   - What symbol statistics exist
   - What strategy symbols are active
   - Where the process fails

## 🔧 Troubleshooting

### Python Command Not Found:
If you get "Python não foi encontrado" error:
1. **Use the full path** to Python
2. **Or use VS Code debugger** instead
3. **Or use Django shell** with debugging

### Import Errors:
Make sure you're running from the project root directory:
```bash
cd D:\1\Projects\tradingSystemDjango
python debug_helpers.py
```

### VS Code Debugger Not Working:
1. **Check Python extension** is installed
2. **Select correct Python interpreter** (Ctrl+Shift+P → "Python: Select Interpreter")
3. **Make sure launch.json** is in the .vscode folder

## 🚀 Quick Debug Workflow

1. **Identify the issue** (e.g., "No active strategy symbols")
2. **Choose your debug method**:
   - VS Code: Set breakpoint, press F5
   - Script: Run `python debug_backtest_enhanced.py`
   - Shell: `python manage.py shell` then `from debug_helpers import debug_66; debug_66()`
3. **Step through the code** using debug commands
4. **Inspect variables** to understand the issue
5. **Fix the problem** and test again

## 📝 Example Debug Session

```bash
$ python debug_backtest_enhanced.py
🐛 Enhanced Django Debugger
==================================================
Available debug functions:
1. debug_backtest_66() - Debug backtest 66 step by step
2. debug_portfolio_logic() - Debug portfolio logic
==================================================
🔍 Starting enhanced debug session for backtest 66...
> /path/to/debug_backtest_enhanced.py(25)debug_backtest_66()
-> try:
(Pdb) n
> /path/to/debug_backtest_enhanced.py(26)debug_backtest_66()
-> backtest = BackTestingStrategy.objects.get(id=66)
(Pdb) n
> /path/to/debug_backtest_enhanced.py(27)debug_backtest_66()
-> print(f"✅ Found backtest: {backtest.strategy.name} (ID: 66)")
(Pdb) p backtest.strategy.name
'Mean Reverting'
(Pdb) c
✅ Found backtest: Mean Reverting (ID: 66)
📊 Trades found: 150
> /path/to/debug_backtest_enhanced.py(35)debug_backtest_66()
-> symbol_stats = SymbolStatistics.objects.filter(backtest=backtest)
(Pdb) c
📈 Symbol Statistics: 0
🎯 Strategy Symbols - Active LONG: 0, Active SHORT: 0
```

This will help you identify exactly where the issue is occurring!
