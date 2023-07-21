echo "Installation started"

echo "Checking the python3..."
if [ -z "$(which python3)" ];
then
    echo "ERROR: python3 is missing"
    exit 1
fi

GITCHECKOUT_CMD="python3 $PWD/main.py"
if [[ "$SHELL" == *"zsh"* ]]; then
    echo "Creating gitcheckout alias in ~/.zshrc..."
    echo alias gitcheckout=\"$GITCHECKOUT_CMD\" >> ~/.zshrc
else
    echo "Creating gitcheckout alias in ~/.bashrc..."
    echo alias gitcheckout=\"$GITCHECKOUT_CMD\" >> ~/.bashrc
fi

echo "Installation finished"