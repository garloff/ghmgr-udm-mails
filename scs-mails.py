#!/usr/bin/env python3
#
# scs-mails.py
#
# This program looks through all github accounts as listed in a
# github-manager org data.yaml file.
# It then queries github for a public mail address.
# It additionally looks through a UCS users file for mail addresses,
# using some fuzzy matching logic for names.
#
# The output will be a CSV file with github acct name, name, mails
#
# (c) Kurt Garloff <scs@garloff.de>, 1/2025
# SPDX-License-Identifier: CC-BY-SA-4.0

# import os
import sys
import getopt
import re
import github
import yaml

SEP = ","


def usage(rc=1):
    "Help"
    print("Usage: scs-mails.py [options] data.yaml users.udm")
    print(" Options: [-m|--mail]            only output a list of mail addresses")
    print("          [-o|--outfile out.csv] write output to out.csv instead of stdout")
    print("          [-p|--pat github.pat]  get mail adrs from github")
    print("          [-h|--help]            this help")
    return rc


class MailUser:
    "An github ORG member"
    def __init__(self, ghnm, name):
        "C'tor"
        self.ghnm = ghnm
        self.name = name
        self.ucsnm = ""
        self.mls = []

    def __str__(self):
        "String representation (CSV)"
        return f"{self.ghnm}{SEP}{self.name}{SEP}{self.ucsnm}{SEP}{SEP.join(self.mls)}"


def parseOrgData(fnm):
    "Read github-manager org data.yaml and return user list"
    users = []
    with open(fnm, 'r', encoding="utf-8") as file:
        y = yaml.safe_load(file)
    for member in y["members"]:
        users.append(MailUser(member["login"], member["name"]))
    return users


def githubMail(user, gh):
    "Try to get github public mail for user and add"
    ghu = gh.get_user(user.ghnm)
    if ghu.email:
        if ghu.email not in user.mls:
            user.mls.append(ghu.email)


class UdmUser:
    "Abstraction of UCS user (as output by udm udm users/user list)"
    def __init__(self, uid, name=""):
        "C'tor"
        self.uid = uid
        self.name = name
        self.gecos = name
        self.mls = []

    def __repr__(self):
        "string representation"
        return f"{self.uid}{SEP}{self.name}{SEP}{self.gecos}{SEP}{SEP.join(self.mls)}"


def readUDM(fnm):
    "parse UDM user dump (LDAP like)"
    uidre = re.compile(r'uid=([^,]*),')
    udm = []
    usr = None
    with open(fnm, "r", encoding="utf-8") as file:
        for ln in file:
            ln = ln.strip('\r\n')
            # A new record
            if ln[:4] == "DN: ":
                m = uidre.match(ln[4:])
                if m:
                    usr = UdmUser(m.group(1))
                    udm.append(usr)
                else:
                    usr = None
                    print(f"Warning: DN line without uid= match: {ln}", file=sys.stderr)
            # If we're not inside a record, ignore
            if not usr:
                continue
            # Parse Name and eMails
            if ln[2:14] == "displayName:":
                usr.name = ln[15:]
            elif ln[2:21] == "mailForwardAddress:":
                if ln[22:] in usr.mls:
                    usr.mls.remove(ln[22:])
                usr.mls.insert(0, ln[22:])
            elif ln[2:9] == "e-mail:":
                if ln[10:] not in usr.mls:
                    usr.mls.append(ln[10:])
            elif ln[2:8] == "gecos:":
                usr.gecos = ln[9:]
    return udm


def normalizeName(nm):
    "Normalize Name to avoid non-ASCII chars and to strip Dr."
    if nm[:3] == "Dr.":
        nm = nm[3:]
    nm = nm.strip(" ")
    nm = nm.replace("ä", "ae")
    nm = nm.replace("ö", "oe")
    nm = nm.replace("ü", "ue")
    nm = nm.replace("Ä", "Ae")
    nm = nm.replace("Ö", "Oe")
    nm = nm.replace("Ü", "Ue")
    nm = nm.replace("ß", "ss")
    nm = nm.replace("é", "e")
    nm = nm.replace("è", "e")
    nm = nm.replace("ë", "e")
    nm = nm.replace("á", "a")
    nm = nm.replace("å", "a")
    nm = nm.replace("æ", "ae")
    nm = nm.replace("œ", "oe")
    nm = nm.replace("ø", "o")
    nm = nm.replace("ĳ", "ij")
    nm = nm.replace("ÿ", "y")
    nm = nm.replace("ý", "y")
    nm = nm.replace("ž", "z")
    nm = nm.replace("š", "s")
    nm = nm.replace("č", "c")
    nm = nm.replace("ç", "c")
    nm = nm.replace("ñ", "n")
    nm = nm.replace("ń", "n")
    nm = nm.replace("ł", "l")
    nm = nm.replace("-", " ")
    return nm


def nameMatch(nm1, nm2):
    "Are these names the same, at least after normalization?"
    if nm1 == nm2:
        return True
    if normalizeName(nm1) == normalizeName(nm2):
        return True
    # We could do more here? Fuzzy Logic?
    return False


def udmMail(user, udm):
    "Search udm database for mail address and add uid and mails if there's a match"
    for udmuser in udm:
        if nameMatch(user.name, udmuser.name) or nameMatch(user.name, udmuser.gecos):
            user.ucsnm = udmuser.uid
            for ml in udmuser.mls:
                user.mls.append(ml)


def main(argv):
    "main entry point"
    # Defaults
    out = sys.stdout
    pat = None
    mailonly = False
    # Option handling
    try:
        (optlist, args) = getopt.gnu_getopt(argv[1:], "ho:p:m",
                                            ("help", "outfile", "pat", "mail"))
    except getopt.GetoptError as exc:
        print("Error:", exc, file=sys.stderr)
        sys.exit(usage())
    for opt in optlist:
        if opt[0] == "-h" or opt[0] == "--help":
            sys.exit(usage(0))
        elif opt[0] == "-o" or opt[0] == "--outfile":
            out = open(opt[1], "w", encoding="utf-8")
        elif opt[0] == "-p" or opt[0] == "--pat":
            pat = opt[1]
        elif opt[0] == "-m" or opt[0] == "--mail":
            mailonly = True

    if not args:
        sys.exit(usage())
    # Create user list
    users = parseOrgData(args[0])
    # Add mails from UDM dump
    if len(args) > 1:
        udm = readUDM(args[1])
        for user in users:
            udmMail(user, udm)
    # Add mails from github
    if pat:
        gha = github.Auth.Token(open(pat, "r").read().strip('\r\n'))
        with github.Github(auth=gha) as gh:
            for user in users:
                githubMail(user, gh)

    for user in users:
        if mailonly:
            if user.mls:
                print(user.mls[0], file=out)
        else:
            print(user, file=out)


# Call main
if __name__ == "__main__":
    main(sys.argv)
