#match simulated sources detected to input ones, computing the reliability and completeness
# of the sample
import numpy as np
import sys
from astropy.io import fits
import matplotlib.pyplot as plt
import time
from ciao_contrib.region.check_fov import FOVFiles

def distance(pointa, pointb):
    xx = np.cos(pointa[1]/180*3.141592)
    return np.sqrt(((pointa[0]-pointb[0])*xx*3600)**2 +((pointa[1]-pointb[1])*3600)**2)

wd='/Users/alberto/Desktop/XBOOTES/'

#take catalog of detected sources (wavdetect, full mosaic 4x4, 5e-5, only bkgmap)
cat1=fits.open(wd+'mosaic_broad_sim_poiss_cat1_3.fits')

ra_k=cat1[1].data['RA']
dec_k=cat1[1].data['DEC']
cts_full=cat1[1].data['TOT']
prob=cat1[1].data['PROB']
r90=cat1[1].data['AV_R90']
flux_k=cat1[1].data['FLUX']
print(len(ra_k))
#cut detected sample at a given probability threshold (1e-3)
cut=1e-3
#prob=np.e**(-detml)

'''
ra_k=ra_k[prob<=cut]
dec_k=dec_k[prob<=cut]
cts_full=cts_full[prob<=cut]
r90=r90[prob<=cut]
#detml=detml[prob<=cut]
flux_k=flux_k[prob<=cut]
prob=prob[prob<=cut]
print(len(ra_k))
sys.exit()
'''
#write out the cut sample
w=open(wd+'cdwfs_broad_sim_poiss_'+str(cut)+'.reg','w')
for i in range(len(ra_k)):
	w.write('circle('+str(ra_k[i])+'d, '+str(dec_k[i])+'d, '+str(r90[i])+'\") #width=2 color=red \n')
w.close()

#take list of sources in input to simulation
(flux_cdwfs,ra_cdwfs,dec_cdwfs)=np.genfromtxt(wd+'poiss_rand_lehmerx20_filtered.dat',unpack=True,skip_header=1)
### NEED TO FILTER THESE SOURCES WITH THE TOTAL FOV OF THE CDWFS, SOME OF THEM ARE OUTSIDE 
### AND CANNOT BE MATCHED BY DEFINITION
#w=open(wd+'poiss_rand_lehmerx20_filtered.dat','w')
#w.write('Flux \t RA \t DEC \n')
#my_obs = FOVFiles('@'+wd+'fov.lis')
#for i in range(len(ra_cdwfs)):
#	myobs = my_obs.inside(ra_cdwfs[i], dec_cdwfs[i])
#	if len(myobs) > 0:
#		w.write(str(flux_cdwfs[i])+' \t '+str(ra_cdwfs[i])+' \t '+str(dec_cdwfs[i])+' \n')
#w.close()
print(len(ra_cdwfs))

#ra_cdwfs=ra_cdwfs[cts_full_cdwfs>=4.]
#dec_cdwfs=dec_cdwfs[cts_full_cdwfs>=4.]
#w=open(wd+'murray_sens/xbootes_broad_cat0_3.reg','w')
#for i in range(len(ra_cdwfs)):
#	w.write('circle('+str(ra_cdwfs[i])+'d, '+str(dec_cdwfs[i])+'d, 20\") #width=2 color=cyan \n')
#w.close()

bins=np.logspace(np.log10(5e-17),np.log10(9e-13),100)
a,b=np.histogram(flux_cdwfs,bins=bins)

bincenters=list((b[i+1]+b[i])/2. for i in range(len(b)-1))
#plt.figure()
#plt.plot(bincenters,a,'go')
#plt.xscale('log')
#plt.yscale('log')
#plt.show()

print('Starting to match...')
t_in=time.time()
#match_rad=5.0
flux_inp,flux_out=[],[]
w=open(wd+'sim_broad_unmatched_3.reg','w')
w2=open(wd+'cdwfs_broad_sim_poiss_matched.dat','w')
unmatched=0
blendings=0
cts=[]
for i in range(len(ra_k)):
	kenter_source=[ra_k[i],dec_k[i]]
	match_rad=1.1*r90[i]
	found=0
	counterparts=[]
	at_least_one=False
	count=0
	for j in range(len(ra_cdwfs)):
		cdwfs_source=[ra_cdwfs[j],dec_cdwfs[j]]
		d=distance(kenter_source,cdwfs_source)
		if d <= match_rad: #found a match
			if found==0: #it's the first
				if flux_k[i]/flux_cdwfs[j] < 10.: #and the flux ratio is less than a factor of 10
					found=1
					flux_inp.append(flux_cdwfs[j])
					flux_out.append(flux_k[i])
					w2.write(str(ra_k[i])+' \t '+str(dec_k[i])+' \t '+str(flux_cdwfs[j])+' \n')
					at_least_one=True
			else: #it's not the first match	
				if flux_k[i]/flux_cdwfs[j] < 10.: #and the flux ratio is less than a factor of 10
					count=count+2
					blendings=blendings+1
					print('Found the '+str(count)+'nd/rd/th counterpart to '+str(kenter_source))
	if found==0:
		unmatched=unmatched+1
		w.write('circle('+str(ra_k[i])+'d, '+str(dec_k[i])+'d, 20\") #width=2 color=cyan \n')
		cts.append(cts_full[i])
		print(ra_k[i],dec_k[i],prob[i])
		if cts_full[i] > 30.0:
			print(ra_k[i],dec_k[i])

w.close()
w2.close()
t_out=time.time()
print(unmatched, 'unmatched')
print(blendings,' blendings')
print(float(t_out-t_in)/60.,' minutes for the match.')

a2,b2=np.histogram(flux_inp,bins=bins)

print(a)
print(a2)
rat=list(float(a2[i])/float(a[i]) for i in range(len(a)))
print(rat)

plt.figure()
plt.plot(bincenters,rat,'k-')
plt.xscale('log')
plt.xlabel('0.5-7 keV Flux [erg cm$^{-2}$ s$^{-1}$]',fontsize=13)
plt.ylabel('Completeness',fontsize=13)
plt.savefig(wd+'cdwfs_broad_completeness.pdf',format='pdf',dpi=1000)
#plt.show()

x=np.linspace(1e-16,1e-12,100)
plt.figure()
plt.plot(flux_inp,flux_out,'r.')
plt.plot(x,x,'k--')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('0.5-7 keV Input Flux [erg cm$^{-2}$ s$^{-1}$]',fontsize=13)
plt.ylabel('0.5-7 keV Output Flux [erg cm$^{-2}$ s$^{-1}$]',fontsize=13)
#plt.hist(cts,bins=100)
#plt.show()
plt.savefig(wd+'cdwfs_broad_Fin-Fout.pdf',format='pdf',dpi=1000)