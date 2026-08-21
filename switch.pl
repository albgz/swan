# --- parsing arguments
$esmf = "FALSE";
$tim = "FALSE";
$jac = "FALSE";
$ffro = "FALSE";
$mpi = "FALSE";
$f95 = "FALSE";
$dos = "FALSE";
$unx = "FALSE";
$cry = "FALSE";
$sgi = "FALSE";
$imp = "FALSE";
$cvi = "FALSE";
$adc = "FALSE";
$coh = "FALSE";
$met = "FALSE";
$ncf = "FALSE";
$mv4 = "FALSE";
while (@ARGV && $ARGV[0] =~ /^-/)
   {
   $option = shift;
   if    ($option eq "-esmf")   {$esmf="TRUE";}
   elsif ($option eq "-timg")   {$tim="TRUE";}
   elsif ($option eq "-jac")    {$jac="TRUE";}
   elsif ($option eq "-fixfront") {$ffro="TRUE";}
   elsif ($option eq "-mpi")    {$mpi="TRUE";}
   elsif ($option eq "-f95")    {$f95="TRUE";}
   elsif ($option eq "-dos")    {$dos="TRUE";}
   elsif ($option eq "-unix")   {$unx="TRUE";}
   elsif ($option eq "-cray")   {$cry="TRUE";}
   elsif ($option eq "-sgi")    {$sgi="TRUE";}
   elsif ($option eq "-impi")   {$imp="TRUE";}
   elsif ($option eq "-cvis")   {$cvi="TRUE";}
   elsif ($option eq "-adcirc") {$adc="TRUE";}
   elsif ($option eq "-coh")    {$coh="TRUE";}
   elsif ($option eq "-metis")  {$met="TRUE";}
   elsif ($option eq "-netcdf") {$ncf="TRUE";}
   elsif ($option eq "-matl4")  {$mv4="TRUE";}
   else { die "$0: unsupported option $option\n"; }
   }

# --- trap unsupported switch combinations
if ($esmf=~/TRUE/ && $adc=~/TRUE/)
{
   die "$0: -esmf and -adcirc is not supported.\n";
}
if ($esmf=~/TRUE/ && $met=~/TRUE/)
{
   die "$0: -esmf and -metis is not supported.\n";
}

# --- make a list of all files
@files = ();
foreach $pattern (@ARGV) {
   if (-e $pattern) {
      push @files, $pattern;
   } else {
      push @files, glob($pattern);
   }
}

# --- change each file if necessary
foreach $file (@files)
{
# --- set output file name
  if ($unx=~/TRUE/)
  {
    $outfile = $file;
    $outfile =~ s/\.ftn90$/.f90/;
    $outfile =~ s/\.ftn$/.f/;
  }
  else
  {
    $outfile = $file;
    $outfile =~ s/\.ftn90$/.f90/;
    $outfile =~ s/\.ftn$/.for/;
  }
# --- process file
  if (   (! -e $outfile)            #outfile doesn't exist
      || (-M $file < -M $outfile) ) #.ftn file recently modified
  {
    open(INPUT, "<", $file) or die "can't open $file: $!\n";
    open(OUTPUT, ">", $outfile) or die "can't open $outfile: $!\n";
    while ($line=<INPUT>)
    {
      $newline=$line;
      # ESMF must be processed first
      if ($esmf=~/TRUE/) {$newline=~s/^!ESMF//;}
      else               {$newline=~s/^!!ESMF//;} #second "!" is negation
      if ($tim=~/TRUE/) {$newline=~s/^!TIMG//;}
      if ($jac=~/TRUE/) {$newline=~s/^!JAC//;}
      else              {$newline=~s/^!WFR//;}
      if ($ffro=~/TRUE/) {$newline=~s/^!FXFRO//;}
      else               {$newline=~s/^!GRAPH//;}
      if ($mpi=~/TRUE/) {$newline=~s/^!MPI//;}
      if ($f95=~/TRUE/) {$newline=~s/^!F95//;}
      if ($dos=~/TRUE/) {$newline=~s/^!DOS//;}
      if ($unx=~/TRUE/) {$newline=~s/^!UNIX//;}
      if ($cry=~/TRUE/) {$newline=~s/^!\/Cray//;}
      if ($sgi=~/TRUE/) {$newline=~s/^!\/SGI//;}
      if ($imp=~/TRUE/) {$newline=~s/^!\/impi//;}
      if ($cvi=~/TRUE/) {$newline=~s/^!CVIS//;}
      if ($adc=~/TRUE/) {$newline=~s/^!ADC//;}
      if ($adc=~/FALSE/) {$newline=~s/^!NADC//;}
      if ($coh=~/TRUE/) {$newline=~s/^!COH//;}
      if ($coh=~/FALSE/){$newline=~s/^!NCOH//;}
      if ($met=~/TRUE/) {$newline=~s/^!METIS//;}
      if ($ncf=~/TRUE/) {$newline=~s/^!NCF//;}
      if ($ncf=~/FALSE/){$newline=~s/^!NNCF//;}
      if ($mv4=~/TRUE/) {$newline=~s/^!MatL4//;}
      if ($mv4=~/FALSE/) {$newline=~s/^!MatL5//;}
      print OUTPUT $newline;
    }
    close(INPUT) or die "can't close $file: $!\n";
    close(OUTPUT) or die "can't close $outfile: $!\n";
  }
}
