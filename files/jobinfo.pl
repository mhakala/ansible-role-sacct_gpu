#!/usr/bin/perl

# small wrapper to get information from /run/gpustats.json and parse those to format that scontrol reads for comment
use POSIX;

if(isdigit($ARGV[0])) {
  $id=$ARGV[0];
  $file="/run/gpustats.json";
}else{
  exit 1;
}

open(INFO, $file) or die("Could not open file.");
foreach $line (<INFO>)  {   
  if($line =~ m/$id.:\s*(\{[^\}]+\})/) {
    $info=$1;
  }
}
close(INFO);

$info =~ s/\"step\":\s*\d+,//;
$info =~s/\s+/ /g;
print "$info\n";

