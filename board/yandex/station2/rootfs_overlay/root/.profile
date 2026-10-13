# ~/.profile - Auto-launch Fish shell on interactive login
if [ -x /usr/bin/fish ] && [ -t 0 ] && [ "$SHELL" != "/usr/bin/fish" ]; then
    export SHELL=/usr/bin/fish
    exec /usr/bin/fish
fi
