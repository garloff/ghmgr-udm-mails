# ghmgr-udm-mails

Find mail addresses for github org members (gh-manager managed) in UCS user directory.

## Why this tool?

For the [SCS](https://scs.community/) [project board](https://docs.scs.community/standards/scs-0005-v1-project-governance)
election, all members of the SCS github organization have active voting rights.
The members of the organization are defined in the
[data.yaml](https://github.com/SovereignCloudStack/github-manager/blob/main/orgs/SovereignCloudStack/data.yaml)
file in github-manager.

In order to use the voting right, users need to receive a link with a token via email.
The election management thus needs a list of email addresses of all voters.

The data in github-manager only contains the github handles and -- in most cases --
the full names of the voters, but no email address.

Some github users have configured a publicly visible email address. This one can be used
and can be queried via the github API, using a
[personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

The other database that contains email addresses is the
[UCS](https://www.univention.com/products/ucs/)/[nextcloud](https://nextcloud.com/)
server that the SCS community has been using since Dec 2019. Mailing lists are also operated there.

Using the full names, github users can be matched with UCS/nextcloud users and the email
address(es) be extracted. (Matching is a bit tricky in presence of titles, umlauts etc.
so some normalization is done.) This is what this script does, creating a .csv file with
github handles, full names, UCS account names and email addresses from github
manager's data.yaml file, the UCS user database dump (`udm user/users list`) and
(optionally) the public mail addresses via the github API.

## Usage

```
Usage: scs-mails.py [options] data.yaml users.udm
 Options: [-m|--mail]            only output a list of mail addresses
          [-o|--outfile out.csv] write output to out.csv instead of stdout
          [-p|--pat github.pat]  get mail adrs from github
          [-h|--help]            this help
```
