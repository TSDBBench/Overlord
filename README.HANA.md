To test SAP HANA Express Edition  some extra steps are necessary.
You will need the JDBC driver from the Hana studio program (ngdbc.jar), make some adjustments to the generator VM and create an own image for the database itself.

Prepare virtual machine images
1. Put ngdbc.jar to /home/vagrant/YCSB-TS/ngdbc.jar in the generator VM image.
2. Create a new VM image and install HANA express edition onto the image.(It is advised to use the same password for all password prompts.)
3. add the data of the created image file to vagrant_files/hana1/files/vagrantconf_db.rb .
4. Substitute <PASSWORD> in  databases/hana1.py with the actual password set in step two. And if needed change the user in the same file.
optional:
5.If you want to test different sorts of tables, change vagrant_files/hana1/files/create_table.mysql

While interpreting the results please keep in mind that SAP HANA is an inmemory database,so disk space values alone are not really comparable.
