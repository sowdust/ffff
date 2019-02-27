# FFFF - FFFF Finds Facebook Friends

Build a partial friends list of a target Facebook account using the "mutual friends" utility.

Requires knowing at least another account having at least one mutual friend with the target.


## Disclaimer

Scraping without written permission is against Facebook [Terms of Services](https://www.facebook.com/apps/site_scraping_tos_terms.php).


## About

Facebook offers a function to list all friends two accounts have in common, called "mutual friends", if at least one of the accounts' lists is visible to the observer.
This function can be applied recursively over all mutual friends found, possibly yielding a larger set of friends.


### Prerequisites

The script works in Python 3 with the libraries `selenium` and `argparse`.

```pip3 install -r requirements.txt```

As of now it supports only Firefox webdriver and requires the [geckodriver executable](https://github.com/mozilla/geckodriver/releases).
Support for more webdrivers can be easily added if necessary.


### Requisites

The script works with Facebook numeric account ids.
There are several ways to find out an account numeric id, including many online services such as [findmyfbid.com](https://findmyfbid.com/) or [graph.tips](http://graph.tips/).

It requires a set of valid credentials (username and password) of a Facebook account to be used for collecting the results.

__Warning__: Accounts used for scraping are not allowed without permission, and can therefore be locked by Facebook anti-scraping mechanisms.

To buid a partial friend list of a target account, the script requires:

* the target account numeric id
* the account id of at least one "pivot" account (ie.: any account with at least one friend in common with the target).


## Usage

Some options (the facebook credentials and the the driver executables) can be hardcoded inside the script source code:
```
FB_USR = 'username@facebook.com'
FB_PWD = 'password'
GECKO_PATH = 'C:\geckodriver.exe'  
```
Otherwise, they can be provided as a command line option.


Pivot accounts can be provided either as a list of integers separated by a space via command line (with the option `--pivots`), or one per row in a file (`--pivots-file`).
A list of accounts to ignore as pivots can be provided as well (`--ignore-file`).

```
usage: ffff.py [-h] [-fu USERNAME] [-fp PASSWORD] [-t TARGET]
               [-p PIVOT [PIVOT ...]] [-o OUTPUT] [-P PIVOTSFILE]
               [-I IGNOREFILE] [-r SESSION] [-q] [-d EXECUTABLE]

Recursively build friends list of Facebook users by exploiting the "mutual
friends" utility.

optional arguments:
  -h, --help            show this help message and exit
  -fu USERNAME, --user USERNAME
                        Username of the Facebook account that will be used for
                        scraping
  -fp PASSWORD, --password PASSWORD
                        Username of the Facebook account that will be used for
                        scraping
  -t TARGET, --target TARGET
                        Numeric id of the target Facebook account
  -p PIVOT [PIVOT ...], --pivots PIVOT [PIVOT ...]
                        Numeric id(s) of the Facebook accounts known to have
                        mutual friends with the target. Their friends list
                        must be public. Can be a single value or a list of
                        values separated by a space.
  -o OUTPUT, --output OUTPUT
                        Specify where to store output (in CSV format)
  -P PIVOTSFILE, --pivots-file PIVOTSFILE
                        Load a list of Facebook ids to use as pivot accounts
                        from file PIVOTSFILE. Numeric ids must be one per
                        line. This option can be used together or in place of
                        --pivots.
  -I IGNOREFILE, --ignore-file IGNOREFILE
                        Load a list of Facebook ids NOT to use as pivot
                        accounts from file IGNOREFILE. Numeric ids must be one
                        per line.
  -r SESSION, --resume SESSION
                        Resume a previous session from file SESSION
  -q, --headless        Run browser in headless mode. No browser window will
                        be shown.
  -d EXECUTABLE, --driver-path EXECUTABLE
                        Path to geckodriver executable

```

### Examples

The following example usage tries to build a subset of the friends list of target account id "00000000", pivoting on account "00000001", and finally storing the results in CSV file "results.csv".


Adding the `-q` option makes the webdriver run in headless mode: no browser window should be shown.

In the example, the Linux geckodriver executable is stored in the current directory. Geckodriver executables can be downloaded from [Mozilla repository](https://github.com/mozilla/geckodriver/releases). If you are using Windows and have downloaded the geckodriver.exe in the current directory, use `--driver-path geckodriver.exe`.

```
python3 ffff.py -t 00000000 -p 00000001 -o results.csv -q --driver-path ./geckodriver
```
The session can be stopped (Ctrl+C) and resumed at a later time:

```
^CSession stored to file session-00000000-20190221232552. Use "--resume session-00000000-20190221232552" to resume from here
```
The result, a list of friends of the target, is provided as a csv file in the form `account id, account name, account url`).


## License

This code is ffffree


