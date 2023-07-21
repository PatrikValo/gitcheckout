# gitcheckout

gitcheckout is customized `git checkout` command.
It is designed to switch between recently used branches very fast.
It allows us to:

**Create a new branch with the description**

Very often I use a branch name with JIRA ID inside. It is great as unique identifier and good reference, but you have to search for JIRA if you want to switch back to some branch. You have to do a extra slow step.

`gitcheckout -b <name> <description>`

gitcheckout requires a human readable description for better trackability.

```bash
$ gitcheckout -b pvalo_personal_branch "implement gitcheckout -l command"
Switched to a new branch 'pvalo_personal_branch'
```

**List latest checkouts**

The most important feature is to print latest checkouts.

`gitcheckout -l` / `gitcheckout --list`

This command allows you to get the latest 10 branches to which you did a checkout action. For each entry there is assigned a unique number in the table.

```bash
$ gitcheckout -l
+ --- + ------------------------------ + ---------------------------------------- +
|  n  | name                           | description                              |
+ --- + ------------------------------ + ---------------------------------------- +
|  0  | pvalo_personal_branch          | implement gitcheckout -l command         |
|  1  | doc2                           | update a README documentation            |
|  2  | doc                            | create a README documentation            |
+ --- + ------------------------------ + ---------------------------------------- +
```

**Switch to branch based on the name**

gitcheckout allows you to do the basic switch to branch with specific name

`gitcheckout <branch_name>`

You can use '-' sign to switch to previous branch as you are probably used to.

```bash
$ gitcheckout -
Switched to branch 'doc2'
```

**Switch to branch based on the number**

Sometimes the previous checkout is not enough and you would like to switch to older checkout.
In that case you have to find the name, write or copy the name and switch.

`gitcheckout -n <checkout_number>`

gitcheckout allows us to do it quicker. The reference number from table comes to play and you can do the switch very fast with just typing the reference number.

```bash
$ gitcheckout -n 2
Switched to branch 'doc'
```

## Installation

**Requirements**

- `bash` or `zsh`
- `python3`

**Installation steps**

```bash
chmod u+x install.sh
```

```bash
./install.sh
```
