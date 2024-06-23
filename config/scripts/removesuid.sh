#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

# Reference: https://gist.github.com/ok-ryoko/1ff42a805d496cb1ca22e5cdf6ddefb0#usrbinchage


chmod u-s /usr/bin/mount
chmod u-s /usr/bin/mount.nfs
chmod u-s /usr/bin/umount

chmod u-s /usr/sbin/unix_chkpwd
setcap cap_dac_read_search,cap_audit_write=ep /usr/sbin/unix_chkpwd

chmod u-s /usr/bin/chage
setcap cap_dac_read_search,cap_audit_write=ep /usr/bin/chage

chmod u-s /usr/bin/chsh
setcap cap_chown,cap_dac_override,cap_fowner,cap_audit_write=ep /usr/bin/chsh

chmod u-s /usr/bin/chfn
setcap cap_chown,cap_dac_override,cap_fowner,cap_audit_write=ep /usr/bin/chfn

chmod u-s /usr/bin/fusermount
chmod u-s /usr/bin/fusermount3

chmod u-s /usr/bin/gpasswd

chmod u-s /usr/bin/newgrp
setcap cap_dac_read_search,cap_setgid,cap_audit_write=ep /usr/bin/newgrp

chmod u-s /usr/libexec/openssh/ssh-keysign
setcap cap_dac_read_search=ep /usr/libexec/openssh/ssh-keysign
