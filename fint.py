import re, os, csv, sys, time
import json, random, argparse

from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options



VERSION = "0.1"
BANNER = """
{0} v. {1} - Fint: Find users who interacted with a profile

by sowdust
""".format(sys.argv[0],VERSION)

BASE_URL = 'https://mbasic.facebook.com'

def log(m): return

def pause(min=2,max=5):
    return round(random.uniform(min,max),1)

def do_login(driver,usr,pwd):

    log('[*] Trying to log in with user %s' % usr)
    driver.get('https://www.facebook.com')
    assert "Facebook" in driver.title
    elem = driver.find_element_by_id('email')
    elem.send_keys(usr)
    elem = driver.find_element_by_id('pass')
    elem.send_keys(pwd)
    elem.send_keys(Keys.RETURN)
    log('[*] Logged in')
    time.sleep(pause(2,3))


def get_stories_urls(html,target):

    # only return stories BY the user 
    user_token = 'id=%s' % target

    links = re.findall('(/story.php\?story_fbid=[^"#]+)',html)
    return ['%s%s'% (BASE_URL,x.replace('&amp;','&')) for x in set(links) if user_token in x]


def get_photos_urls(html):
    links = re.findall('(/photo.php\?fbid=[^"#]+)',html)
    return ['%s%s'% (BASE_URL,x.replace('&amp;','&')) for x in set(links)]


def get_all_photos(driver,target,limit=100):

    url = 'https://mbasic.facebook.com/%s/photos' % target
    driver.get(url)
    time.sleep(pause())
    see_all = re.findall('<a href="([^"#]+)">See All</a>',driver.page_source)

    photos = []
    if not see_all:
        return photos
    else:
        driver.get(BASE_URL + see_all[0].replace('&amp;','&'))

    while len(photos) < limit:

        photos += get_photos_urls(driver.page_source)
        see_more = re.findall('<a href="(.[^"#]*)"><span>See More Photos</span></a>',driver.page_source)
        if not see_more:
            see_more = re.findall('<a href="(.[^"#]*)">Show more</a>',driver.page_source)
        if see_more:
            url = BASE_URL + see_more[0].replace('&amp;','&')
            time.sleep(pause())
            driver.get(url)
        else:
            break
    return photos


def get_all_stories(driver,target,limit=100):

    url = 'https://mbasic.facebook.com/%s?v=timeline' % target
    driver.get(url)

    stories = []

    while len(stories) < limit:
        stories += get_stories_urls(driver.page_source,target)
        see_more = re.findall('<a href="(.[^"#]*)"><span>See More Stories</span></a>',driver.page_source)
        if not see_more:
            see_more = re.findall('<a href="(.[^"#]*)">Show more</a>',driver.page_source)
        if see_more:
            url = BASE_URL + see_more[0].replace('&amp;','&')
            time.sleep(pause())
            driver.get(url)
        else:
            break
    return stories


def get_all_comments(driver,url,limit=200,cur_length=0):

    if cur_length >=limit: 
        return []

    driver.get(url)
    html = driver.page_source.encode("utf-8",errors='replace').decode("utf-8", errors="replace")

    commenters = parse_commenters(html)
    cur_length += len(commenters)
    more_comments_url = re.findall('<div class=".[^"]*" id="see_next_[0-9]+"><a href="(.[^"]*)">',html)
    more_comments_url = ['%s%s'% (BASE_URL,x.replace('&amp;','&')) for x in more_comments_url]

    if(more_comments_url) and limit > cur_length:
        time.sleep(pause())
        url = more_comments_url[0]
        commenters += get_all_comments(driver,url,limit,cur_length=cur_length)
    return commenters


# given a driver on a story.php page, extracts all users who have reacted
# takes only 1st level reactions (not consideringr reactions to comments etc.)
def get_all_reactions(driver,url,reactions_per_page=999,limit=2000,cur_length=0):

    if cur_length >=limit: 
        return []

    driver.get(url)
    html = driver.page_source.encode("utf-8",errors='replace').decode("utf-8", errors="replace")

    reactions = parse_likers(html)
    cur_length += len(reactions)

    reaction_urls = re.findall('(/ufi/reaction/profile/browser/(?!.*(?:reaction_type|total_count=0)).[^"]*)',html)
    reaction_urls = ['%s%s'% (BASE_URL,x.replace('&amp;','&').replace('?limit=10','?limit=%d' % reactions_per_page)) for x in reaction_urls]

    if(reaction_urls) and limit > cur_length:
        time.sleep(pause())
        url= reaction_urls[0]
        reactions += get_all_reactions(driver,url,reactions_per_page,limit,cur_length)
    return reactions


# Given a story.php page, return a list of (url, display name)
def parse_commenters(html):
    return re.findall('<h3><a class="[^"]+" href="([^"]+)\?r[^"]*">([^<]*)</a>',html)


# Given a "reactions" page ufi/reaction/profile/browser/, returns a list of (url, display name) 
def parse_likers(html):
    return re.findall('<h3 class=".[^"]*"><a href="(.[^"]*)[^"]*">(.[^<]*)</a></h3>',html)


def profile_picture(driver,target_username):

    url = '%sphoto.php?fbid=%s' % (BASE_URL,target_username)
    driver.get(url)
    commenters = parse_commenters(driver.page_source)


# given a list of [username, name] returns a list of [id, name, username]
def fill_user_ids(driver,users):

    res = []
    c = 0
    msg = '[*] Retreiving user ids... '
    try:
        for u in users:
            c += 1
            msg = '%s[*] Retreiving user ids... %d of %d' % ('\r'*len(msg),c,len(users))
            print(msg, end='\r')
            time.sleep(pause())
            fbid = get_user_id(driver,u[0])
            user = (fbid, u[1], u[0])
            res.append(user)
    except (KeyboardInterrupt, SystemExit):
        print('[!] KeyboardInterrupt received. Exiting...')
        return res
    except Exception as ex:
        print('[!] Error while retrieving user ids')
        print(ex)
        return res
    return res


# given a username, finds the fb user id from the source of the profile page
def get_user_id(driver,username):

    url = 'https://www.facebook.com/%s' % username.replace('/','')
    driver.get(url)
    fbid = re.findall('fb://(profile|page)/([0-9]+)',driver.page_source)
    if fbid:
        return fbid[0][1]
    else:
        print('[!] Error while getting id of user %s' % username)
        return -1


def get_username(driver,userid):

    url = 'https://www.facebook.com/%s' % userid
    driver.get(url)
    time.sleep(pause())
    return driver.current_url.split('/')[-1].split('?')[0]


def parse_args():

    parser = argparse.ArgumentParser(description='Find users who interacted with a Facebook profile.')
    parser.add_argument('-fu', '--user', metavar='USERNAME', type=str, help='Username of the Facebook account that will be used for scraping')
    parser.add_argument('-fp', '--password', metavar='PASSWORD', type=str, help='Username of the Facebook account that will be used for scraping')
    parser.add_argument('-t', '--target', metavar='TARGET', type=str, help='Username or numeric id of the target Facebook account')
    parser.add_argument('-ls', '--limit-stories', metavar='LIMIT', type=int, default=20, help='Max number of stories to analyze')
    parser.add_argument('-lp', '--limit-photos', metavar='LIMIT', type=int, default=20, help='Max number of photos to analyze')
    parser.add_argument('-lr','--limit-reactions', metavar='LIMIT', default=1000, type=int, help='Max number of reactions to analyze for each story')
    parser.add_argument('-lc','--limit-comments', metavar='LIMIT', default=100, type=int, help='Max number of comments to analyze for each story')
    parser.add_argument('-o','--output', metavar='OUTPUTFILE', type=str, help='Specify the name of the pivots output file')
    parser.add_argument('-csv','--csv-output', metavar='CSVOUTPUTFILE', type=str, help='Store output file also in CSV format')
    parser.add_argument('-q', '--headless', action='store_true', help='Run browser in headless mode. No browser window will be shown.')
    parser.add_argument('-d','--driver-path', metavar='EXECUTABLE', type=str, help='Path to geckodriver executable')
    args = parser.parse_args(args=None if len(sys.argv) > 1 else ['--help'])

    return args


def print_statistics(commenters,reactions):
    print('-'*78)
    print(' ' * 34, end=' ')
    print('STATISTICS')
    print('-'*78)

    print('Most comments:')
    for u in Counter(commenters).most_common():
        print('[%d]\t%s (%s)' % (u[1],u[0][1],u[0][0]))
    print()
    print('Most reactions:')
    for u in Counter(reactions).most_common():
        print('[%d]\t%s (%s)' % (u[1],u[0][1],u[0][0]))
    print()
    print('Total:')
    for u in Counter(commenters + reactions).most_common():
        print('[%d]\t%s (%s)' % (u[1],u[0][1],u[0][0]))
    print()


def store_csv(users,csv_file_path):
    print('[*] Storing users in csv file %s' % csv_file_path)
    with open(csv_file_path, mode='w',newline='',encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['id','name','url'])
        for u in users:
            writer.writerow(u)


def store_pivots(users,path):
    print('[*] Storing users id in file %s' % path)
    with open(path, 'w') as f:
        for u in users:
            f.write('%s\n' % u[0])


def check_file_exists(file):
    yes = {'yes','y', 'ye'}
    if os.path.isfile(file):
        print('[!] Warning: output file %s already exists. Do you want to overwrite? [y/N]' % file, end=' ')
        choice = input().lower()
        if choice not in yes:
            sys.exit(0)            


def main():

    print(BANNER)
    args = parse_args()

    options = Options()
    if args.headless : options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=args.driver_path,options=options)

    do_login(driver,args.user,args.password)

    if args.target.isdigit():
        target_id = args.target
        target_username = get_username(driver,target_id)
    else:
        target_id = get_user_id(driver,args.target)
        target_username = args.target

    print('[*] Selected target: %s (%s)' % (target_username,target_id))


    urls_to_visit = []
    commenters = []
    reactions = []


    print('[*] Getting photos links... ', end =" ")
    photos = get_all_photos(driver,target_username,args.limit_photos)[:args.limit_photos]
    print('%d photos found' % len(photos))
    print('[*] Getting stories links... ', end =" ")
    stories = get_all_stories(driver,target_id,args.limit_stories)[:args.limit_stories]
    print('%d stories found' % len(stories))

    print('[*] Retreiving users who have interacted... press Ctrl+C when you have enough')

    msg = ''
    try:
        for url in photos + stories:

            commenters += parse_commenters(driver.page_source)
            if len(commenters) < args.limit_comments:
                commenters += get_all_comments(driver,url,limit=args.limit_comments)

            if len(reactions) < args.limit_reactions:
                reactions += get_all_reactions(driver,url,limit=args.limit_reactions)

            users = list(set(reactions).union(set(commenters)))
            msg = '%sUnique users: %d        Comments: %d        Reactions: %d' % ('\r'*len(msg),len(users),len(commenters),len(reactions))
            print(msg, end='\r')

    except (KeyboardInterrupt, SystemExit):
        print('[!] KeyboardInterrupt received. %d users retrieved' % len(users))

    reactions = reactions[:args.limit_reactions]
    commenters = commenters[:args.limit_comments]
    users = list(set(reactions).union(set(commenters)))
    print_statistics(commenters,reactions)
    users = fill_user_ids(driver,users)

    if args.output:
        store_pivots(users,args.output)
    else:
        store_pivots(users,'%s-pivots.txt' % target_id)

    if args.csv_output:
        store_csv(users,args.csv_output)

    print('[*] Found %d comments and %d reactions from %d unique users ' % (len(commenters),len(reactions),len(users)))

    driver.close()


if __name__ == '__main__':
    main()