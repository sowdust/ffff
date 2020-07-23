import re, os, csv, sys, time
import json, random, argparse
import io, pickle, codecs
import networkx as nx, builtins

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

FB_USR = ''
FB_PWD = ''
GECKO_PATH = ''


VERSION = "0.2"
BANNER = """
{0} v. {1} - FFFF: FFFF Finds Facebook Friends

by sowdust
""".format(sys.argv[0],VERSION)


class RestrictedUnpickler(pickle.Unpickler):
    
    safe_builtins = {
        'range',
        'complex',
        'set',
        'frozenset',
        'slice',
        'dict'
    }

    def find_class(self, module, name):
        if module in "builtins" and name in self.safe_builtins:
            return getattr(builtins, name)
        elif module == "networkx.classes.graph" and name == "Graph":
            return getattr(nx, name)
        # Forbid everything else.
        raise pickle.UnpicklingError("Cannot unserialize '%s.%s'. Forbidden" %
                                     (module, name))


def restricted_loads(s):
    s = codecs.decode(s.encode(), "base64")
    return RestrictedUnpickler(io.BytesIO(s)).load()


def pause(min=2,max=5):
    return round(random.uniform(min,max),1)


def log(msg):    return


def profile_picture_url(fbid,size=200):
    return 'https://graph.facebook.com/%d/picture?width=%d' % (fbid,size)


def do_login(driver,usr,pwd):

    log('[*] Trying to log in with user %s' % usr)
    driver.get('https://www.facebook.com')
    try:
        elem = driver.find_element_by_id('email')
        elem.send_keys(usr)
        elem = driver.find_element_by_id('pass')
        elem.send_keys(pwd)
    except NoSuchElementException:
        elem = driver.find_element_by_name('email')
        elem.send_keys(usr)
        elem = driver.find_element_by_name('pass')
        elem.send_keys(pwd)
    except Exception as ex:
        print('[!] Error while logging in:')
        print(ex)
        sys.exit(0)
    elem.send_keys(Keys.RETURN)
    time.sleep(pause(2,3))


def check_login(driver):
    time.sleep(pause(2,3))
    if 'href="https://www.facebook.com/?sk=ff"' not in driver.page_source:
        print('[!] Not logged in. Did you use valid credentials?')
        sys.exit(0)
    else:
        log('[*] Logged in')
    

def get_target_info(target,driver):
    driver.get('https://www.facebook.com/%s' % target)
    time.sleep(pause())
    try:
        name = re.findall('"Person","name":"([^"]+)"',driver.page_source)[0]
    except:
        name = 'TARGET'
    return [name,driver.current_url]


def check_file_exists(file):
    yes = {'yes','y', 'ye'}
    if os.path.isfile(file):
        print('[!] Warning: output file %s already exists. Do you want to overwrite? [y/N]' % file, end=' ')
        choice = input().lower()
        if choice not in yes:
            sys.exit(0)


def get_friends(driver,usr1,usr2,graph,store_weights,url='https://www.facebook.com/browse/mutual_friends/?uid=%s&node=%s'):

    friends = []
    final_url = url % (usr1,usr2)
    log('[*] Trying to retrieve url %s' % final_url)

    attempts = 0

    while attempts < 5:
        try:
            driver.get(final_url)
            break
        except TimeoutException as ex:
            print('[!] TimeoutException. Attempt #%d' % attempts)
            attempts +=1
            pause(attempts*10,attempts*10)

    # Scroll to bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        time.sleep(pause(1,2))
    
    try:
        users = driver.find_elements_by_css_selector("div[class='fsl fwb fcb']")

        for user in users:
            s = user.get_attribute('innerHTML')

            try:
                uid = re.findall('/ajax/hovercard/user.php\?id=([0-9]*)(?:"|&amp;)',s)
                url = re.findall('href=[\'"]?([^\'" >]+)',s)
                name = re.findall('>[.*]?([^<]+)',s)
            except:
                print('[!] Error! Cannot read data from HTML page')
                continue

            friend = {}
            try:
                friend['name'] = name[0].encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            except:
                friend['name'] = 'decoding error'
            friend['id'] = int(uid[0])
            friend['url'] = re.sub('(\?|\&amp.+)fref.*','',url[0])
            friends.append(friend)

            graph = update_graph(graph,usr1,usr2,friend,store_weights)
            

    except Exception as ex:
        print('[!] Error! %s' % ex)
        raise

    return friends


def update_graph(G,usr1,usr2,friend,store_weights):

    G.add_node(friend['id'], label=friend['name'], url=friend['url'], img=profile_picture_url(friend['id']))

    for usr in [usr1,usr2]:

        if G.has_edge(usr,friend['id']) and store_weights:
            # increment weight
            G[usr][friend['id']]['weight'] += 1
        else:
            # add new edge
            G.add_edge(usr,friend['id'], weight=1)

    return G


def get_all_friends(target,pivots,driver,writer,file,tested,friends,args,session_args,graph,store_weights):
    
    msg = ''
    try:
        while pivots:

            time.sleep(pause())
            fid = pivots[0]
            count_new = count_old = 0
            for g in get_friends(driver,target,fid,graph,store_weights):
                # add all new friends to queue of pivot points
                if g['id'] not in tested and g['id'] not in pivots:
                    pivots.append(g['id'])
                # update list of friends found
                if g not in friends:
                    count_new += 1
                    friends.append(g)
                    if writer:
                        writer.writerow(g)
                else:
                    count_old += 1

            file.flush()
            tested.append(fid)
            del(pivots[0])

            msg = '%s%d Found      %d Tested      %d To test      Last pivot: %d' % ('\r'*len(msg),len(friends),len(tested),len(pivots),fid)
            print(msg, end='\r')

    except (KeyboardInterrupt, SystemExit):
        print('\n[!] KeyboardInterrupt received. Quitting.\n')
        interrupt(target,file,driver,pivots,tested,friends,session_args,graph)
    except Exception as ex:
        # traceback.print_exc()
        print('\n\n[!] Error: %s. Quitting.\n' % ex)
        interrupt(target,file,driver,pivots,tested,friends,session_args,graph)

    print('')
    return friends


def load_ids_from_file(file):
    if not os.path.isfile(file):
        print('[!] Error. File not found %s' % file)
        sys.exit(0)
    with open(file) as f:
        tested = [int(x) for x in f.readlines()]
    return tested


def interrupt(target,csv_file,driver,pivots,tested,friends,session_args,graph):

    cur_time = time.strftime('%Y%m%d%H%M%S')
    session = {}
    session['time'] = cur_time
    session['args'] =  session_args
    session['tested'] = tested
    session['pivots'] = pivots
    session['friends'] = friends
    session['output'] = csv_file.name
    session['graph'] = codecs.encode(pickle.dumps(graph), "base64").decode()
    session_file = 'session-%s-%s' % (target,cur_time)

    print('\nExiting. Storing state to file...\n')

    with open(session_file, 'w') as outfile:
        json.dump(session, outfile)
    if not csv_file.closed:
        csv_file.flush()
        csv_file.close()
    nx.write_gexf(graph,session_args['graph_output'])
    driver.quit()

    print('...session state: %s' % session_file)
    print('...friends found: %s' % csv_file.name)
    print('...friendship graph: %s' % session_args['graph_output'])
    print('\nUse \"--resume %s\" to restart from here. Bye.\n' % session_file)

    sys.exit(0)


def parse_args():

    parser = argparse.ArgumentParser(description='Recursively build friends list of Facebook users by exploiting the "mutual friends" utility.')
    parser.add_argument('-fu', '--user', metavar='USERNAME', type=str, help='Username of the Facebook account that will be used for scraping')
    parser.add_argument('-fp', '--password', metavar='PASSWORD', type=str, help='Username of the Facebook account that will be used for scraping')
    parser.add_argument('-t', '--target', metavar='TARGET', type=int, help='Numeric id of the target Facebook account')
    parser.add_argument('-p','--pivots', metavar='PIVOT', nargs='+', type=int, help='Numeric id(s) of the Facebook accounts known to have mutual friends with the target. Their friends list must be public. Can be a single value or a list of values separated by a space.')
    parser.add_argument('-o','--output', metavar='OUTPUTFILE', type=str, help='Specify where to store list of friends found in CSV format')
    parser.add_argument('-g','--graph-output', metavar='GRAPHFILE', type=str, help='Specify where to store graph in GEXF (Graph Exchange XML Format) format')
    parser.add_argument('-P','--pivots-file', metavar='PIVOTSFILE', type=str, help='Load a list of Facebook ids to use as pivot accounts from file PIVOTSFILE. Numeric ids must be one per line. This option can be used together or in place of --pivots.')
    parser.add_argument('-I','--ignore-file', metavar='IGNOREFILE', type=str, help='Load a list of Facebook ids NOT to use as pivot accounts from file IGNOREFILE. Numeric ids must be one per line.')
    parser.add_argument('-r','--resume', metavar='SESSION', type=str, help='Resume a previous session from file SESSION')
    parser.add_argument('-q', '--headless', action='store_true', help='Run browser in headless mode. No browser window will be shown.')
    parser.add_argument('-w', '--store-weights', action='store_true', help='Assign weights based on how many times a relationship is observed.')
    parser.add_argument('-d','--driver-path', metavar='EXECUTABLE', type=str, help='Path to geckodriver executable')
    args = parser.parse_args(args=None if len(sys.argv) > 1 else ['--help'])

    return args


def main():

    print(BANNER)
    args = parse_args()

    usr = args.user if args.user else FB_USR
    pwd = args.password if args.password else FB_PWD
    if not usr or not pwd:
        print('[!] Error: valid facebook credentials must be provided')
        sys.exit(0)

    pivots = args.pivots if args.pivots else []
    if args.pivots_file:
        pivots_from_file = load_ids_from_file(args.pivots_file)
        print('Loaded %d facebook ids to use for pivoting.' % len(pivots_from_file))
        pivots += pivots_from_file

    if args.resume:

        if not os.path.isfile(args.resume):
            print('[!] Error: session file %s not found' % args.resume)
            sys.exit(0)

        print('Restoring session from file %s' % args.resume)
        with open(args.resume,'r') as session_json:
            session = json.loads(session_json.read())
            target = session['args']['target']
            if args.target and args.target != target:
                print('[!] Error: target provided differs from the one stored in session file')
                sys.exit(0)            
            tested = session['tested']
            # you can add pivots from command line
            pivots = list((set(pivots) - set(session['tested']))| set(session['pivots']))   
            friends = session['friends']
            csv_file_path = args.output if args.output else session['output']
            csv_write_mode = 'w'
            options = Options()
            if args.headless or session['args']['headless']: options.add_argument("--headless")
            driver_path = session['args']['driver_path'] if session['args']['driver_path']  else GECKO_PATH
            store_weights = session['args']['store_weights']
            session_args = session['args']
            graph = restricted_loads(session['graph'])
            graph_output = session_args['graph_output']

    else:

        session_args = vars(args)
        del session_args['password']
        del session_args['user']

        target = args.target
        if not args.target:
            print('\n[!] Error. You must specify the ID of the target Facebook profile')
            sys.exit(0)

        if not args.output:
            csv_file_path = '%d-friends.csv' % target
            print('Output file not specified. Results will be stored in %s' % csv_file_path)
            session_args['output'] = csv_file_path
        else:
            csv_file_path = args.output

        if not args.graph_output:
            graph_output = '%d-friends.gexf' % target
            print('Graph Output file not specified. Results will be stored in %s' % graph_output)
            session_args['graph_output'] = graph_output
        else:
            graph_output = args.graph_output
        
        options = Options()
        if args.headless: options.add_argument("--headless")
        driver_path = args.driver_path if args.driver_path  else GECKO_PATH
        if not driver_path:
            print('\n[!] Error: the path to the geckodriver executable file must be provided')
            print('Geckodriver executables can be downloaded from https://github.com/mozilla/geckodriver/releases')
            sys.exit(0)

        if args.ignore_file:
            tested = load_ids_from_file(args.ignore_file)
            print('Loaded %d facebook ids already used for pivoting. They will be skipped if found again.' % len(tested))
        else:
            tested = []

        if not pivots:
            print('\n[!] Error. Empty pivot list. If the target user friend list is public, just use its id as pivot (add "-p %d")' % target)
            sys.exit(0)

        store_weights = args.store_weights
        friends = []
        csv_write_mode = 'w'
        graph = nx.Graph()


    print('')    
    check_file_exists(csv_file_path)
    check_file_exists(graph_output)

    # fetch and write friends
    driver = webdriver.Firefox(executable_path=driver_path,options=options)
    start = time.time()
    do_login(driver,usr,pwd)
    check_login(driver)

    if 'target_name' not in session_args.keys():
        [session_args['target_name'],session_args['target_url']] = get_target_info(target,driver)
        graph.add_node(target, label=session_args['target_name'], url=session_args['target_url'],img=profile_picture_url(target))

    print('\nFetching friends of target user "%s" (%d)...\n' % (session_args['target_name'], target))
    

    with open(csv_file_path, mode=csv_write_mode,newline='',encoding='utf-8') as csv_file:

        fieldnames = ['id', 'name', 'url']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if csv_write_mode == 'w':
            writer.writeheader()
            # if there are friends to write (ie from a previous session)
            if friends:
                for f in friends:
                    writer.writerow(f)
                csv_file.flush()

        friends = get_all_friends(target,pivots,driver,writer,csv_file,tested,friends,args,session_args,graph,store_weights)

    end = time.time()

    lengths = [len(x['name']) for x in friends]
    for f in friends:
        print("{: >10} {: >20} {: >20}".format(f['id'],f['name'],f['url']))

    print('Found a total of %d friends in %.2f' % (len(friends), end-start))
    interrupt(target,csv_file,driver,pivots,tested,friends,session_args,graph)


if __name__ == '__main__':
    main()
