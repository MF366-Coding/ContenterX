import os
import cxsetup
import colorama


def flag_function():
    print('Flag marked.')

flag = cxsetup.FlagMarker(flag_function)


def create_interpreter(data: str):
    space, actual = data.split('\n', maxsplit=1)
    
    inter = cxsetup.Interpreter(actual, int(space), flag, 'apt', 'echo', 'npm')
    
    return inter
    
    
def init_interpreter(i: cxsetup.Interpreter):
    i.init()
    return 0
    
    
def test1():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Comments
    - Outputs
    - Newlines
    - Statements
    """
    
    init_interpreter(create_interpreter("""30
# Comment
COUT ?? "lol";  ENDL2;
//TERMINATE;
COUT ?? "test";
"""))


def test2():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Outputs
    - Terminations
    """
    
    init_interpreter(create_interpreter("""30
# Comment
COUT ?? "lol";
TERMINATE;
COUT ?? "test";
"""))
    
    
def test3():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Newlines
    - Terminations with specified error code
    """
    
    init_interpreter(create_interpreter("""30
# Comment
COUT ?? "lol";
ENDL;
TERMINATE ?? 3;
COUT ?? "test";
"""))


def test4():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Basic inputs
    - Newlines
    """
    
    x = create_interpreter("""30
# Comment
COUT ?? "lol";
ENDL;
CIN;
ENDL;
""")
    init_interpreter(x)
    return x._cache.cache

    
def test5():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Limited Inputs
    - Cache Grabs
    - Newlines across CIN and COUT
    - Comments
    - Single-character Inputs
    """
    
    x = create_interpreter("""50
// Comment
CIN ?? 4;
CIN ?? 1;
COUT ?? "Your input: " ?? c0:5e:1:3:b; ENDL;
TERMINATE;
""")
    init_interpreter(x)
    return x._cache.cache
 
   
def test6():
    """
    Behaves as expected.
    
    What is being tested here includes (but isn't limited to):
    - Advanced Inputs with SAFECIN
    - Newlines across CIN and COUT
    - Cache Grabs
    - Input Messages
    - Single-character Inputs
    """
    
    x = create_interpreter("""50
// Comment
SAFECIN ?? 4;
CIN ?? 1 ?? "Do you wish to run X command? (y or n): ";
COUT ?? "Your input: " ?? c0:4e:1:3:l;
ENDL;
TERMINATE;
""")
    init_interpreter(x)
    return x._cache.cache
    

def test7():
    x = create_interpreter("""50
// Comment
SAFECIN ?? 4;
FORE ?? "YELLOW";
COUT ?? "Do you wish to run X command (y or n)?";
FORE ?? "RESET"; ENDL;
YAYORNAY;
COUT ?? "Your input: " ?? c0:4l:1:3:r; ENDL;
TERMINATE;
""")
    init_interpreter(x)
    return x._cache.cache


def test8():
    x = create_interpreter("""50
// Comment
SAFECIN ?? 4;
COUT ?? "Your input: " ?? c0:4l:1:3:r;
CLEAR;
TERMINATE;
""")
    init_interpreter(x)
    return x._cache.cache


def check_cache(cache: cxsetup.Cache, test_id: int):
    print(colorama.Fore.GREEN, end='')
    print(f'\nCache for Test {test_id}', end='')
    print(colorama.Style.RESET_ALL)
    print(str(cache, 'utf-8'), end='')


if __name__ == '__main__':
    while True:
        print(f'''\n{cxsetup.Fore.YELLOW}\n      ███              █████████  █████ █████       ███████████                   █████               ███
 ███ ░███  ███        ███░░░░░███░░███ ░░███       ░█░░░███░░░█                  ░░███           ███ ░███  ███
░░░█████████░        ███     ░░░  ░░███ ███        ░   ░███  ░   ██████   █████  ███████        ░░░█████████░
  ░░░█████░         ░███           ░░█████             ░███     ███░░███ ███░░  ░░░███░           ░░░█████░
   █████████        ░███            ███░███            ░███    ░███████ ░░█████   ░███             █████████
 ███░░███░░███      ░░███     ███  ███ ░░███           ░███    ░███░░░   ░░░░███  ░███ ███       ███░░███░░███
░░░  ░███ ░░░        ░░█████████  █████ █████          █████   ░░██████  ██████   ░░█████       ░░░  ░███ ░░░
     ░░░              ░░░░░░░░░  ░░░░░ ░░░░░          ░░░░░     ░░░░░░  ░░░░░░     ░░░░░             ░░░

                                                                                                                                                                                                                                         
MF366{cxsetup.Fore.RESET} *{cxsetup.Fore.GREEN} MIT License{cxsetup.Fore.RESET}''')
        
        test = int(input(f'{cxsetup.Fore.MAGENTA}Select a test to perform: {cxsetup.Fore.RESET}'))
        os.system('clear')
        
        match test:
            case 1:
                print(colorama.Fore.YELLOW, end='')
                print('Test 1', end='')
                print(colorama.Style.RESET_ALL)
                test1()
        
            case 2:
                print(colorama.Fore.YELLOW, end='')
                print('Test 2', end='')
                print(colorama.Style.RESET_ALL)
                test2()
        
            case 3:
                print(colorama.Fore.YELLOW, end='')
                print('Test 3', end='')
                print(colorama.Style.RESET_ALL)
                test3()
            
            case 4:
                print(colorama.Fore.YELLOW, end='')
                print('Test 4', end='')
                print(colorama.Style.RESET_ALL)
                c = test4()
    
                input(f"{cxsetup.Fore.MAGENTA}\nPress any key to view the cache...\033[8m")
                print(cxsetup.Style.RESET_ALL, end='')
        
                check_cache(c, 4)
        
            case 5:
                print(colorama.Fore.YELLOW, end='')
                print('Test 5', end='')
                print(colorama.Style.RESET_ALL)
                c = test5()
                
                input(f"{cxsetup.Fore.MAGENTA}\nPress any key to view the cache...\033[8m")
                print(cxsetup.Style.RESET_ALL, end='')
        
                check_cache(c, 5)
        
            case 6:
                print(colorama.Fore.YELLOW, end='')
                print('Test 6', end='')
                print(colorama.Style.RESET_ALL)
                c = test6()
                
                input(f"{cxsetup.Fore.MAGENTA}\nPress any key to view the cache...\033[8m")
                print(cxsetup.Style.RESET_ALL, end='')
        
                check_cache(c, 6)
        
            case 7:
                print(colorama.Fore.YELLOW, end='')
                print('Test 7', end='')
                print(colorama.Style.RESET_ALL)
                c = test7()
                
                input(f"{cxsetup.Fore.MAGENTA}\nPress any key to view the cache...\033[8m")
                print(cxsetup.Style.RESET_ALL, end='')
        
                check_cache(c, 7)
    
            case _:
                os.system('clear')
                
                print(f'''\n{cxsetup.Fore.YELLOW}\n      ███              █████████  █████ █████       ███████████                   █████               ███
 ███ ░███  ███        ███░░░░░███░░███ ░░███       ░█░░░███░░░█                  ░░███           ███ ░███  ███
░░░█████████░        ███     ░░░  ░░███ ███        ░   ░███  ░   ██████   █████  ███████        ░░░█████████░
  ░░░█████░         ░███           ░░█████             ░███     ███░░███ ███░░  ░░░███░           ░░░█████░
   █████████        ░███            ███░███            ░███    ░███████ ░░█████   ░███             █████████
 ███░░███░░███      ░░███     ███  ███ ░░███           ░███    ░███░░░   ░░░░███  ░███ ███       ███░░███░░███
░░░  ░███ ░░░        ░░█████████  █████ █████          █████   ░░██████  ██████   ░░█████       ░░░  ░███ ░░░
     ░░░              ░░░░░░░░░  ░░░░░ ░░░░░          ░░░░░     ░░░░░░  ░░░░░░     ░░░░░             ░░░


MF366{cxsetup.Fore.RESET} *{cxsetup.Fore.GREEN} MIT License{cxsetup.Fore.RESET}''')
                print(f'{cxsetup.Fore.BLUE}Thank you! {cxsetup.Fore.RED}<3{cxsetup.Style.RESET_ALL}')
                break

        print(end='\n\n')
        input(f"{cxsetup.Fore.MAGENTA}Press any key to continue...\033[8m")
        print(cxsetup.Style.RESET_ALL, end='')
        os.system('clear')

    os._exit(0)
