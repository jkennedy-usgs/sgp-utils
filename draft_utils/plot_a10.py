def plt_a10(g_min,sigma_set,all_sets,accepted_sets,rejected_sets,fname,pyplot):
    fig = pyplot.figure()
    ax=fig.add_subplot(111)
    print rejected_sets
    
    if not rejected_sets:
        ax.errorbar(all_sets,g_min,sigma_set,fmt='ro')
    else:
        print fname
        print g_min
        pd =  [g_min[i-1] for i in accepted_sets]
        sd =  [sigma_set[i-1] for i in accepted_sets]
        ax.errorbar(accepted_sets,pd,sd,fmt='ko')
        pd =  [g_min[i-1] for i in rejected_sets]
        sd =  [sigma_set[i-1] for i in rejected_sets]
        ax.errorbar(rejected_sets,pd,sd,fmt='ro')
    ax.set_xlim([0,max(all_sets)+1])
    
    name = fname.replace(".set.txt","")
    pyplot.title(name)
    #~ print fname
    pyplot.savefig(name+'.png')
