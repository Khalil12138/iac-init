#!/bin/bash

# Script description and usage
# Usage: ./changeimage.sh
# Description:
# base64 encode this script for code transfer " base64 changeimage.sh -w 0 "
# one-liner background execution: SCRIPT='L3Njcmlwd...' && nohup bash -c "echo $SCRIPT | base64 -d | bash"

# Copyright: (c) 2022, Linus Xu <linxu3@cisco.com>

# Global variable for the filename
# FILESERVER="http://fileserver/Images/ACI/5/5.0"  << a file server path
# FILENAME="aci-n9000-dk9.15.0.2h.bin"   <<< get from global environemnt vars

# Log file setup
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOGFILE="/tmp/script_${TIMESTAMP}.log"
exec > >(tee "$LOGFILE") 2>&1
echo "Script execution started: $(date)"


# Function to execute a script and check for "Done" in the output
execute_and_check() {
    # Execute script passed as parameter and capture the output
    output=$("$@") # Using "$@" to allow passing whole command with parameters

    echo $output
    # Check if output contains "Done"
    if [[ $output == *"Done"* ]]; then
        echo "$1 executed successfully."
    else
        echo "[!] Error: $1 did not complete successfully."
        exit 1
    fi
}


# Function to check if a directory is empty
check_directory_empty() {
    dir=$1
    if [ "$(find "$dir" -mindepth 1 -print -quit 2>/dev/null)" ]; then
        echo "[!] Error: Directory $dir is not empty."
        exit 1
    else
        echo "Directory $dir is empty. Continuing..."
    fi
}

# Function to find and delete files starting with a specific prefix
delete_files_with_prefix() {
    prefix=$1
    echo "deleteing all images"
    rm -f $prefix
}

# Function to download a file and check if it was saved successfully
download_and_check() {
    url=$1
    destination="/bootflash/$FILENAME"
    wget "$url" -O "$destination" 2>/dev/null
    if [ -f "$destination" ]; then
        echo "File '$destination' downloaded and saved successfully."
    else
        echo "[!] Error: File '$destination' could not be downloaded."
        exit 1
    fi
}

# Function to check for the existence of a file and specific content within
check_file_and_content() {
    file_path=$1
    search_content="boot $FILENAME"
    if [ ! -f "$file_path" ]; then
        echo "[!] Error: File $file_path does not exist."
        exit 1
    elif ! grep -q "$search_content" "$file_path"; then
        echo "[!] Error: The required content '$search_content' is not in $file_path."
        exit 1
    else
        echo "File $file_path contains the required content."
    fi
}

# Main logic of the script
main() {
    echo "[+] CHECKING target image information"
    echo "TargetImage: $FILENAME"
    echo "FileServer: $FILESERVER"

    echo "[+] CLEANING configs & bootvars"
    execute_and_check "setup-clean-config.sh"
    execute_and_check "clear-bootvars.sh"

    echo "[+] CHECKING grub directory information"
    check_directory_empty "/mnt/cfg/0/boot/grub/"
    check_directory_empty "/mnt/cfg/1/boot/grub/"

    echo "[+] DELETING & DOWNLOAD image"
    delete_files_with_prefix "/bootflash/aci-n9000*"
    download_and_check "$FILESERVER/$FILENAME"

    echo "[+] SETINGUP bootvars"
    output=$(bash -c "setup-bootvars.sh $FILENAME")   #  "$@"  in not work
    echo $output
    if [[ $output == *"Done"* ]]; then
        echo "setup-bootvars.sh executed successfully."
    else
        echo "[!] Error: setup-bootvars.sh did not complete successfully."
        exit 1
    fi

    echo "[+] CHECKING if menu.lst.local files exist and contain the required boot entry"
    check_file_and_content "/mnt/cfg/0/boot/grub/menu.lst.local"
    check_file_and_content "/mnt/cfg/1/boot/grub/menu.lst.local"

    echo "[+]All checks passed. Continue to reboot..."
    vsh -c "reload"
}

# Script entry point
main "$@"
echo "Script execution finished: $(date)"