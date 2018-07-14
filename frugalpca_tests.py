import pandas as pd
import numpy as np
import frugalpca as fp
import subprocess
import os.path
from sklearn.cluster import KMeans

def plot_results(pref_ref, pref_stu):
    pcs_ref = np.loadtxt(pref_ref + '_ref.pcs')
    pcs_stu_sp = np.loadtxt(pref_stu + '_stu_sp.pcs')
    pcs_stu_ap = np.loadtxt(pref_stu + '_stu_ap.pcs')
    pcs_stu_oadp = np.loadtxt(pref_stu + '_stu_oadp.pcs')
    popu_ref = np.loadtxt(pref_ref + '.popu', dtype=np.object)[:,2]
    popu_stu_pred_sp = np.loadtxt(pref_stu + '_pred_sp.popu', dtype=np.object)[:,2]
    popu_stu_pred_ap = np.loadtxt(pref_stu + '_pred_ap.popu', dtype=np.object)[:,2]
    popu_stu_pred_oadp = np.loadtxt(pref_stu + '_pred_oadp.popu', dtype=np.object)[:,2]
    method_list = ['sp', 'ap', 'oadp']
    pcs_stu_list = [pcs_stu_sp, pcs_stu_ap, pcs_stu_oadp]
    popu_stu_list = [pcs_stu_pred_sp, pcs_stu_pred_ap, pcs_stu_pred_oadp]
    fp.plot_pcs(pcs_ref, pcs_stu_list, popu_ref, popu_stu_list, method_list, out_pref=pref_stu)


def test_standardize():
    print('Testing standardize...')
    x = np.array([[0.0,1.0,2.0],
                  [2,2,2],
                  [2,3,2],
                  [0,1,3]])
    x_standardized_crct = np.array([[-1.22474487,0,1.22474487],
                                    [0,0,0],
                                    [0,0,0],
                                    [-1,1,0]])
    x_mean_crct = np.array([1,2,2,0.5]).reshape((-1,1))
    x_std_crct = np.array([0.81649658,1.,1.,0.5]).reshape((-1,1))
    x_mean, x_std = fp.standardize(x, miss=3)
    assert np.allclose(x, x_standardized_crct)
    assert np.allclose(x_mean, x_mean_crct)
    assert np.allclose(x_std, x_std_crct)
    print('Passed!')

    y = np.array([[ 1.,  0.,  1.],
                  [ 0., 3.,  0.],
                  [ 2.,  2.,  0.],
                  [3.,  0.,  0.]])
    y_standardized_crct = np.array([[ 0., -1.,  0.],
                                    [-1., 0, -1.],
                                    [ 0.,  0., -1.],
                                    [0, -1., -1.]])
    y_standardized_crct = np.array([[ 0.        , -1.22474487,  0.        ],
                                    [-2.        ,  0.        , -2.        ],
                                    [ 0.        ,  0.        , -2.        ],
                                    [ 0.        , -1.        , -1.        ]])
    fp.standardize(y, x_mean_crct, x_std_crct, miss=3)
    assert np.allclose(y, y_standardized_crct)

def add_pure_stu():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    ref_merged_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR_merge_ukb_EUR_pure'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR'
    sturef_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100_sturef_kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    pure_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_pure'
    stu_filepref_chunk = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100'
    impure_filepref_chunk = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100/ukb_snpscap_kgn_bial_orphans_pred_EUR_impure_nchunks100'
    n_chunks = 100
    n_pure_samples = 200
    popu_purity_threshold = 0.99
    n_clusters = 6

    # Create popu for pure study samples
    # Find samples whose purity is greater than popu_purity_threshold
    popu_df = pd.read_table(sturef_filepref+'_pred_ap.popu', header=None)
    proba = popu_df[3]
    popu_is_pure = proba > popu_purity_threshold
    assert np.any(popu_is_pure)
    popu_pure_df = popu_df.loc[popu_is_pure]
    popu_pure = popu_pure_df[2]

    # Select the top nearest n_pure_samples individuals in each population by distance to neighbors
    popu_pure_unique = np.unique(popu_pure)
    popu_pure_near_df = popu_pure_df[0:0]
    for pp in popu_pure_unique:
        popu_pure_this_df = popu_pure_df.loc[popu_pure==pp]
        popu_pure_this_near_ind = np.argsort(popu_pure_this_df[4])[:n_pure_samples]
        popu_pure_this_near_df = popu_pure_this_df.iloc[popu_pure_this_near_ind]
        popu_pure_near_df = pd.concat((popu_pure_near_df, popu_pure_this_near_df), axis=0)
    for i in range(popu_pure_near_df.shape[0]):
        popu_pure_near_df.iloc[i,2] += '-borrowed'
    popu_pure_near_df = popu_pure_near_df.iloc[:,:3]
    popu_pure_near = popu_pure_near_df[2]
    print("New samples:")
    print(np.unique(popu_pure_near, return_counts=True))
    popu_pure_near_df.to_csv(pure_filepref+'.popu', sep='\t', header=False, index=False)

    # # Create bed, bim, fam for pure study samples
    # subprocess.run(
    #         ['plink', '--keep-allele-order', '--make-bed',
    #         '--indiv-sort', 'file', pure_filepref+'.popu',
    #         '--bfile', stu_filepref,
    #         '--keep', pure_filepref+'.popu',
    #         '--out', pure_filepref])

    # Merge pure study samples with reference samples
    subprocess.run(
        ['plink', '--keep-allele-order', '--indiv-sort', 'none', '--make-bed',
        '--bfile', ref_filepref,
        '--bmerge', pure_filepref+'.bed', pure_filepref+'.bim', pure_filepref+'.fam',
        '--out', ref_merged_filepref])
    fp.concat_files([ref_filepref+'.popu', pure_filepref+'.popu'], ref_merged_filepref+'.popu')
    if os.path.isfile(ref_merged_filepref+'_ref.pcs'):
        os.remove(ref_merged_filepref+'_ref.pcs')

    merged_popu_df = pd.read_table(ref_merged_filepref+'.popu', header=None)
    merged_popu_df.columns = ['fid', 'iid', 'popu']
    merged_pcs = fp.run_pca(ref_merged_filepref, None, method='sp', load_saved_ref_decomp=True, plot_results=True)[0]
#     merged_df['cluster'] = pd.Series(merged_cluster, index=merged_df.index)
#     merged_popu_cluster = merged_df[['popu', 'cluster']].groupby('popu').agg(lambda x:x.value_counts().index[0])
#     ori_clusters = []
#     for index, row in merged_popu_cluster.iterrows():
#         if row['popu'][-8:] != 'borrowed':
#             ori_clusters += [row['cluster']]
#     ori_clusters = list(set(ori_clusters))
#     # Dangerous: for debugging only !!!!!!!
#     ori_clusters = ['0', '1', '2', '4']
#     ori_df = merged_df[merged_df['cluster'] is in ori_clusters]

 
    # Remove pure study samples from study samples
    filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_pred_EUR'
    subprocess.run(
        ['plink', '--keep-allele-order', '--indiv-sort', 'none', '--make-bed',
         '--bfile', filepref,
         '--remove', pure_filepref+'.popu',
         '--out', filepref+'_impure'])

    # # Remove pure study samples from study samples
    # for i in range(n_chunks):
    #     stu_filepref_chunk_this = stu_filepref_chunk + '_' + str(i).zfill(fp.SAMPLE_SPLIT_PREF_LEN)
    #     os.makedirs(impure_filepref_chunk, exist_ok=True)
    #     impure_filepref_chunk_this = impure_filepref_chunk + '/' + os.path.basename(impure_filepref_chunk) + '_' + str(i).zfill(fp.SAMPLE_SPLIT_PREF_LEN)
    #     subprocess.run(
    #         ['plink', '--keep-allele-order', '--indiv-sort', 'none', '--make-bed',
    #         '--bfile', stu_filepref_chunk_this,
    #         '--remove', pure_filepref+'.popu',
    #          '--out', impure_filepref_chunk_this])
    #     os.remove(impure_filepref_chunk_this+'.log')

def test_online_svd_procrust():
    np.random.seed(21)
    # def test_svd_online():
    print('Testing svd_online and procrustes...')

    # # For debugging only
    # # For comparing with the R script written by Shawn
    # X = np.loadtxt('test_X.dat')
    # b = np.loadtxt('test_b.dat').reshape((-1,1))
    # p, n = X.shape

    # Generate testing matrices
    p = 1000
    n = 200
    X = np.random.normal(size = p * n).reshape((p,n))
    b = np.random.normal(size = p).reshape((p,1))
    np.savetxt('tmp/test_X.dat', X)
    np.savetxt('tmp/test_b.dat', b)

    # Center reference data
    X_mean = np.mean(X, axis = 1).reshape((p,1))
    X -= X_mean
    # Nonrmalize referencd data
    X_norm = np.std(X, axis = 1).reshape((p,1))
    X_norm[X_norm == 0] = 1
    X /= X_norm

    # Center study data
    b -= X_mean
    b /= X_norm

    # Parameters for onlineSVD
    svd_online_dim = 100 # Number of PC's calculated by online SVD
    PC_new_dim = 20 # Number of PC's we want for each new sample
    PC_ref_dim = 4 # Number of PC's for the reference group
    assert PC_new_dim <= svd_online_dim
    assert PC_ref_dim <= PC_new_dim

    # Decompose the training matrix
    U, d, Vt = np.linalg.svd(X, full_matrices = False)
    V = Vt.transpose()
    PC_ref = V[:, :PC_ref_dim]
    # Subset the PC scores since we only need the first k PC's
    U1 = U[:, :svd_online_dim]
    d1 = d[:svd_online_dim]
    V1 = V[:, :svd_online_dim]
    d2, PC_new = fp.svd_online(U1, d1, V1, b, PC_new_dim)

    # Test if the result is close enough
    trueAns = np.linalg.svd(np.concatenate((X,b),axis=1))[2].transpose()[:,:PC_new_dim]
    for i in range(trueAns.shape[1]):
        assert \
            abs(np.max(PC_new[:,i] - trueAns[:,i])) < 0.05 or \
            abs(np.max(PC_new[:,i] + trueAns[:,i])) < 0.05 # online_svd can flip the sign of a PC
    print('Passed!')

    print('Testing procrustes...')
    PC_new_head, PC_new_tail = PC_new[:-1, :], PC_new[-1, :].reshape((1,PC_new_dim))
    PC_ref_fat = np.zeros(n * PC_new_dim).reshape((n, PC_new_dim))
    PC_ref_fat[:, :PC_ref_dim] = PC_ref
    np.savetxt('tmp/test_PC_ref.dat', PC_ref)
    np.savetxt('tmp/test_PC_ref_fat.dat', PC_ref_fat)
    np.savetxt('tmp/test_PC_new_head.dat', PC_new_head)
    # Test procrustes with the same dimension
    R, rho, c = fp.procrustes(PC_ref_fat, PC_new_head)
    # PC_new_tail_trsfed = PC_new_tail @ R * rho + c
    # PC_new_tail_trsfed = PC_new_tail_trsfed.flatten()[:PC_ref_dim]
    subprocess.run(['make', 'procrustes.o'], stdout=subprocess.PIPE)
    subprocess.run(['./procrustes.o'], stdout=subprocess.PIPE)
    R_trace = np.loadtxt('tmp/procrustes_A.dat')
    rho_trace = np.loadtxt('tmp/procrustes_rho.dat')
    c_trace = np.loadtxt('tmp/procrustes_c.dat')
    assert np.allclose(R_trace, R)
    assert np.allclose(rho_trace, rho)
    assert np.allclose(c_trace, c)
    # Test procrustes with different dimensions
    R_diffdim, rho_diffdim, c_diffdim = fp.procrustes_diffdim(PC_ref, PC_new_head)
    R_diffdim_trace = np.loadtxt('tmp/pprocrustes_A.dat')
    rho_diffdim_trace = np.loadtxt('tmp/pprocrustes_rho.dat')
    c_diffdim_trace = np.loadtxt('tmp/pprocrustes_c.dat')
    assert np.allclose(R_diffdim_trace, R_diffdim)
    assert np.allclose(rho_diffdim_trace, rho_diffdim)
    assert np.allclose(c_diffdim_trace, c_diffdim)
    print('Passed!')


def test_pca(pref_ref, pref_stu, cmp_trace=True, load_pcs=False, load_popu=True, assert_results=False, pref_out_trace=None, dim_ref=4, plot_dim=4, plot_size=None, plot_title=None, plot_color_stu=None, plot_legend=True, alpha_stu=0.4, plot_centers=False, hdpca_n_spikes=None, n_clusters=None, load_saved_ref_decomp=True):
    print('Reference: ' + pref_ref)
    print('Study: ' + pref_stu)
    popu_filename_ref = pref_ref + '.popu'
    subpopu_filename_ref = pref_ref + '_sub.popu'
    base_ref = os.path.basename(pref_ref)
    dir_stu = os.path.dirname(pref_stu)
    pref_out = pref_stu + '_sturef_' + base_ref
    if pref_out_trace is None:
        pref_out_trace = pref_out
    pcs_trace_ref_filename = pref_out_trace + '.RefPC.coord'
    pcs_trace_stu_filename = pref_out_trace + '.ProPC.coord'
    dim_ref = 4
    log_level = 'info'
    use_memmap = False
    load_saved_ref_decomp = True

    if load_pcs:
        pcs_ref = np.loadtxt(pref_ref + '_ref.pcs')
        pcs_stu_sp = np.loadtxt(pref_out + '_stu_sp.pcs')
        pcs_stu_ap = np.loadtxt(pref_out + '_stu_ap.pcs')
        # pcs_stu_oadp = np.loadtxt(pref_out + '_stu_oadp.pcs')

        if n_clusters is None:
            popu_ref = np.loadtxt(pref_ref + '.popu', dtype=np.object)[:,2]
        else:
            fam_ref = pd.read_table(pref_ref+'.fam', header=None, delimiter=' ').iloc[:,:2]
            assert fam_ref.shape[0] == pcs_ref.shape[0]
            popu_ref = fp.pred_popu_ref(pcs_ref, n_clusters, out_filename=pref_ref+'_pred.popu', rowhead_df=fam_ref)

        if load_popu:
            popu_stu_pred_sp = np.loadtxt(pref_out + '_pred_sp.popu', dtype=np.object)[:,2]
            popu_stu_pred_ap = np.loadtxt(pref_out + '_pred_ap.popu', dtype=np.object)[:,2]
            # popu_stu_pred_oadp = np.loadtxt(pref_out + '_pred_oadp.popu', dtype=np.object)[:,2]
        else:
            fam_stu = pd.read_table(pref_stu+'.fam', header=None, delimiter=' ').iloc[:,:2]
            assert fam_stu.shape[0] == pcs_stu_sp.shape[0]
            popu_stu_pred_sp = fp.pred_popu_stu(pcs_ref, popu_ref, pcs_stu_sp, pref_out+'_pred_sp.popu', fam_stu)[0]
            popu_stu_pred_ap = fp.pred_popu_stu(pcs_ref, popu_ref, pcs_stu_ap, pref_out+'_pred_ap.popu', fam_stu)[0]
            # popu_stu_pred_oadp = fp.pred_popu_stu(pcs_ref, popu_ref, pcs_stu_oadp, pref_out+'_pred_oadp.popu', fam_stu)[0]
    else:
        pcs_ref, pcs_stu_ap, popu_ref, popu_stu_pred_ap = fp.run_pca(pref_ref, pref_stu, method='ap', dim_ref=dim_ref, hdpca_n_spikes=hdpca_n_spikes, load_saved_ref_decomp=load_saved_ref_decomp)[:4]
        pcs_ref, pcs_stu_sp, popu_ref, popu_stu_pred_sp = fp.run_pca(pref_ref, pref_stu, method='sp', dim_ref=dim_ref, load_saved_ref_decomp=load_saved_ref_decomp)[:4]
        # pcs_ref, pcs_stu_oadp, popu_ref, popu_stu_pred_oadp = fp.run_pca(pref_ref, pref_stu, method='oadp', dim_ref=dim_ref, load_saved_ref_decomp=load_saved_ref_decomp)[:4]


    pcs_min = np.vstack((pcs_ref, pcs_stu_ap)).min(axis=0)
    pcs_max = np.vstack((pcs_ref, pcs_stu_ap)).max(axis=0)
    plot_lim = np.vstack((pcs_min, pcs_max)) * 1.20
    fp.plot_pcs(pcs_ref, pcs_stu_sp, popu_ref, popu_stu_pred_sp, 'sp', out_pref=pref_out, plot_lim=plot_lim, plot_dim=plot_dim, plot_size=plot_size, plot_title=plot_title, plot_color_stu=plot_color_stu, plot_legend=plot_legend, alpha_stu=alpha_stu, plot_centers=plot_centers)
    fp.plot_pcs(pcs_ref, pcs_stu_ap, popu_ref, popu_stu_pred_ap, 'ap', out_pref=pref_out, plot_lim=plot_lim, plot_dim=plot_dim, plot_size=plot_size, plot_title=plot_title, plot_color_stu=plot_color_stu, plot_legend=plot_legend, alpha_stu=alpha_stu, plot_centers=plot_centers)
    # fp.plot_pcs(pcs_ref, pcs_stu_oadp, popu_ref, popu_stu_pred_oadp, 'oadp', out_pref=pref_out, plot_lim=plot_lim, plot_dim=plot_dim, plot_size=plot_size, plot_title=plot_title, plot_color_stu=plot_color_stu, plot_legend=plot_legend, alpha_stu=alpha_stu, plot_centers=plot_centers)

    if cmp_trace:
        pcs_ref_trace = fp.load_trace(pcs_trace_ref_filename, isref=True)
        pcs_stu_trace = fp.load_trace(pcs_trace_stu_filename)
        for i in range(dim_ref):
            corr = np.correlate(pcs_ref[:,i], pcs_ref_trace[:,i])
            sign = np.sign(corr)
            pcs_ref_trace[:,i] *= sign
            pcs_stu_trace[:,i] *= sign
        popu_stu_pred_trace = fp.pred_popu_stu(pcs_ref_trace, popu_ref, pcs_stu_trace)[0]
        fp.plot_pcs(pcs_ref, pcs_stu_trace, popu_ref, popu_stu_pred_trace, 'adp', out_pref=pref_out, plot_lim=plot_lim, plot_dim=plot_dim, plot_size=plot_size, plot_title=plot_title, plot_color_stu=plot_color_stu, plot_legend=plot_legend, alpha_stu=alpha_stu, plot_centers=plot_centers)

    if cmp_trace:
        print('Accuracy comparison (procrustes, ADP, geocenter): ')
        print('Ref:')
        print(fp.procrustes_similarity(pcs_ref_trace, pcs_ref))
        print(np.linalg.norm(pcs_ref_trace - pcs_ref))
        print('SP:')
        print(fp.procrustes_similarity(pcs_stu_trace, pcs_stu_sp))
        print(np.linalg.norm(pcs_stu_trace - pcs_stu_sp))
        print(fp.geocenter_similarity(pcs_stu_sp, popu_stu_pred_sp, pcs_ref, popu_ref))
        print('AP:')
        print(fp.procrustes_similarity(pcs_stu_trace, pcs_stu_ap))
        print(np.linalg.norm(pcs_stu_trace - pcs_stu_ap))
        print(fp.geocenter_similarity(pcs_stu_ap, popu_stu_pred_ap, pcs_ref, popu_ref))
        # print('OADP:')
        # print(fp.procrustes_similarity(pcs_stu_trace, pcs_stu_oadp))
        # print(np.linalg.norm(pcs_stu_trace - pcs_stu_oadp))
        # print(fp.geocenter_similarity(pcs_stu_oadp, popu_stu_pred_oadp, pcs_ref, popu_ref))
        print('ADP:')
        print(fp.procrustes_similarity(pcs_stu_trace, pcs_stu_trace))
        print(np.linalg.norm(pcs_stu_trace - pcs_stu_trace))
        print(fp.geocenter_similarity(pcs_stu_trace, popu_stu_pred_trace, pcs_ref, popu_ref))

        if assert_results:
            assert smlr_trace_ref > 0.99
            assert smlr_trace_sp > 0.99
            assert smlr_trace_ap > 0.99
            assert smlr_trace_oadp > 0.99
            assert np.allclose(pcs_ref, pcs_ref_trace, 1e-3, 1e-3)
            assert np.allclose(pcs_stu_sp, pcs_stu_trace, 5e-1, 5e-2)
            assert np.allclose(pcs_stu_ap, pcs_stu_trace, 1e-1, 5e-2)
            assert np.allclose(pcs_stu_oadp, pcs_stu_trace, 1e-1, 5e-2)

def test_pca_subpopu(pref_ref, pref_stu, popu_name_this, cmp_trace=True, load_pcs=False, plot_size=None, plot_title=None):
    bashout=subprocess.run(['bash', 'keep_popu.sh', pref_ref, pref_stu, popu_name_this], stdout=subprocess.PIPE)
    pref_ref_this, pref_stu_this = bashout.stdout.decode('utf-8').split('\n')[-3:-1]
    test_pca(pref_ref_this, pref_stu_this, cmp_trace=cmp_trace, load_pcs=load_pcs, plot_size=plot_size, plot_title=plot_title)

def convert_ggsim(i):
    n = 1000 + i * 500
    filepref = '../data/ggsim'+str(n)+'/ggsim'+str(n)+'_100000_'+str(n)+'_2_1_100_0'
    fp.trace2bed(filepref)
    filepref = '../data/ggsim'+str(n)+'/ggsim'+str(n)+'_100000_'+'200'+'_2_1_100_1'
    fp.trace2bed(filepref)

def test_pca_500k_EUR():
    pref_ref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb'
    pref_stu = '../data/ukb/ukb_snpscap_kgn_bial_orphans'
    test_pca_subpopu(pref_ref, pref_stu, 'EUR', cmp_trace=False)

def test_pca_array(pref_ref, pref_stu, method, n_chunks, i):
    if type(method) is int:
        method = {0:'oadp', 1:'ap', 2:'sp'}[method]
    pref_stu_this = fp.split_bed_indiv(pref_stu, n_chunks, i)
    fp.run_pca(pref_ref, pref_stu_this, method=method)

def test_merge_array_results():

    # n_chunks = 10
    # ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb'
    # stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_nchunks10/ukb_snpscap_kgn_bial_orphans_5c_nchunks10'
    # cmp_trace=True
    # traceout_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_sturef_kgn_bial_orphans_snps_ukb_snpscap_ukb'

    # n_chunks = 100
    # ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb'
    # stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_nchunks100/ukb_snpscap_kgn_bial_orphans_nchunks100'
    # cmp_trace=False
    # traceout_filepref=None

    n_chunks = 100
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100/ukb_snpscap_kgn_bial_orphans_pred_EUR_nchunks100'
    cmp_trace=False
    traceout_filepref=None

    # n_chunks = 100
    # ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR_merge_ukb_EUR_pure'
    # stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_impure_nchunks100/ukb_snpscap_kgn_bial_orphans_pred_EUR_impure_nchunks100'
    # cmp_trace=False
    # traceout_filepref=None

    # fp.merge_array_results(ref_filepref, stu_filepref, 'sp', n_chunks)
    # fp.merge_array_results(ref_filepref, stu_filepref, 'ap', n_chunks)
    # fp.merge_array_results(ref_filepref, stu_filepref, 'oadp', n_chunks)
    test_pca(ref_filepref, stu_filepref, cmp_trace=cmp_trace, load_pcs=True, load_popu=False, assert_results=False, plot_centers=False, plot_size=(12,4), hdpca_n_spikes=4)

def test_split_bed_indiv():
    filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c'
    n_chunks = 10
    i = 9
    fp.split_bed_indiv(filepref, n_chunks, i)

def test_pca_ggsim():
    dim_ref = 4
    for i in range(5):
        n = 1000 + i * 500
        pref_ref = '../data/ggsim'+str(n)+'/ggsim'+str(n)+'_100000_'+str(n)+'_2_1_100_0'
        pref_stu = '../data/ggsim'+str(n)+'/ggsim'+str(n)+'_100000_'+'200'+'_2_1_100_1'
        test_pca(pref_ref, pref_stu, cmp_trace=True, load_pcs=True, dim_ref=dim_ref, plot_title=str(n), plot_size=(6,6), plot_color_stu='k', plot_legend=True, alpha_stu=0.9, plot_dim=2, plot_centers=True)

def test_pca_5c():
    pref_ref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb'
    pref_stu = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c'
    test_pca(pref_ref, pref_stu, cmp_trace=True, load_pcs=True, load_popu=False, plot_size=(12,4))

def test_pca_5c_EUR():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_pred_EUR'
    test_pca(ref_filepref, stu_filepref, cmp_trace=True, load_pcs=False, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4, load_saved_ref_decomp=False)

def test_pca_EUR_pure():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_pure'
    test_pca(ref_filepref, stu_filepref, cmp_trace=False, load_pcs=False, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4)

def test_pca_5c_EUR_impure():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR_merge_ukb_EUR_pure'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_pred_EUR_impure'
    test_pca(ref_filepref, stu_filepref, cmp_trace=False, load_pcs=False, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4, load_saved_ref_decomp=False)

def test_pca_5c_EUR_impure_predrefpopu():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR_merge_ukb_EUR_pure'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_pred_EUR_impure'
    test_pca(ref_filepref, stu_filepref, cmp_trace=False, load_pcs=True, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4, n_clusters=5)

def test_pca_EUR_pure_homogen():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_pred_EUR_pure_homogen'
    test_pca(ref_filepref, stu_filepref, cmp_trace=False, load_pcs=True, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4)


def test_pca_5c_EUR_impure_ref_homogen():
    ref_filepref = '../data/kgn/kgn_bial_orphans_snps_ukb_snpscap_ukb_EUR_merge_ukb_EUR_pure_homogen'
    stu_filepref = '../data/ukb/ukb_snpscap_kgn_bial_orphans_5c_pred_EUR_impure'
    test_pca(ref_filepref, stu_filepref, cmp_trace=False, load_pcs=False, load_popu=False, assert_results=False, plot_size=(12,4), hdpca_n_spikes=4)
