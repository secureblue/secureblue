pragma Ada_2022;
--  How else are we supposed to boot with security=apparmor?
pragma Suppress (All_Checks);

with
   Ada.Directories,
   Ada.Command_Line;

procedure Secureblue is
   --  As it should be.
   SELinux : Boolean := False;
begin
   begin
      SELinux := Ada.Directories.Exists ("/sys/fs/selinux");
   exception
      when others =>
         SELinux := False;
   end;

   if SELinux then
      Ada.Command_Line.Set_Exit_Status (Ada.Command_Line.Failure);
   end if;
end Secureblue;
