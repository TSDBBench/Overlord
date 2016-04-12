# Workaround for mitchellh/vagrant#1867
# Can't be outsourced in other file
if ARGV[1] and \
   (ARGV[1].split('=')[0] == "--provider" or ARGV[2])
  $provider = (ARGV[1].split('=')[1] || ARGV[2])
else
  $provider = (ENV['VAGRANT_DEFAULT_PROVIDER'] || :virtualbox).to_sym
end