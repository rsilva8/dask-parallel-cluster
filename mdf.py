import numpy as np
from scipy.special import gamma

def mdf_dask_tall_eval(data_dict):
    JE = 0 
     
    beta_ = data_dict['beta_']
    eta_ = data_dict['eta_']
    lambda_ = data_dict['lambda_']
    nu_ = data_dict['nu_']
    a_ = data_dict['a_']
    y_sub = data_dict['y_sub']
    
    _, N = y_sub.shape
   
    D, t1 = np.linalg.eig(y_sub @ y_sub.T)
    A = ((t1 * (1 / D[None,:])) @ t1.T) @ y_sub
    z_k = np.sum(y_sub * A, axis=0)
    z_k_beta = z_k**beta_

    JE += (lambda_ * (((N-1)*a_)**beta_)/N) * np.sum(z_k_beta)
    
    return JE


def mdf_dask_tall(client,Y,K):
    
    beta_ = np.ones(K)
    eta_ = np.ones(K)
    lambda_ = 0.5*np.ones(K)
    nu_ = (2*eta_ + len(Y) - 2)/(2*beta_)
    a_ = (lambda_**(-1/beta_) * gamma(nu_ + 1/beta_)) / (len(Y) * gamma(nu_))

    _, N = Y[0].shape
    
    data_map = []
    
    for kk in range(K):
        y_sub = np.zeros((len(Y),N))
        tot = 0
        for mm in range(len(Y)):
            ix = tot + 1
            y_sub[ix-1,:] = Y[mm][kk,:]
            tot = tot + 1
            
        data_map.append(client.map(mdf_dask_tall_eval,[{'beta_':beta_[kk],
                                                       'eta_':eta_[kk],
                                                       'lambda_':lambda_[kk],
                                                       'nu_':nu_[kk],
                                                       'a_':a_[kk],
                                                       'y_sub':y_sub}]))

    return client.submit(np.sum,data_map)

def mdf(Y,K):
    JE = 0 
    
    beta_ = np.ones(K)
    eta_ = np.ones(K)
    lambda_ = 0.5*np.ones(K)
    nu_ = (2*eta_ + len(Y) - 2)/(2*beta_)
    a_ = (lambda_**(-1/beta_) * gamma(nu_ + 1/beta_)) / (len(Y) * gamma(nu_))

    _, N = Y[0].shape
    
    for kk in range(K):
        y_sub = np.zeros((len(Y),N))
        tot = 0
        for mm in range(len(Y)):
            ix = tot + 1
            y_sub[ix-1,:] = Y[mm][kk,:]
            tot = tot + 1

        D, t1 = np.linalg.eig(y_sub @ y_sub.T)
        A = ((t1 * (1 / D[None,:])) @ t1.T) @ y_sub
        z_k = np.sum(y_sub * A, axis=0)
        z_k_beta = z_k**beta_[kk]
        
        JE += (lambda_[kk] * (((N-1)*a_[kk])**beta_[kk])/N) * np.sum(z_k_beta)
        
    return JE
        
'''        if O.eta(kk) ~= 1
            JF = JF + (1 - O.eta(kk)) * (log(O.N-1)+log(O.a(kk))) + ((1 - O.eta(kk))/O.N) * sum(log(z_k));
        end
        JC = JC + sum(log(D)); % Moved  -0.5*log(O.N-1)*sum(O.d) to fc below

    #     % Gradient:
        if nargout > 1:
    #         % Number of dimensions in each modality (for subspace kk):
            z_k = ( (2*O.beta(kk)*O.lambda(kk) ...
                * (((O.N-1)*O.a(kk))^(O.beta(kk)))/O.N)*z_k_beta ...
                + (2*(1-O.eta(kk))/(O.N*O.a(kk))) )./(z_k + eps);
            B = bsxfun(@times, A, z_k);
            C = -(B * y_sub');
            cc = sub2ind(size(C),1:length(C),1:length(C));
            C(cc) = C(cc) + 1;

            t1 = cell(size(O.W));

                  tot = 0;
                    for mm in O.M
                        ix = tot + (1:O.d_k{mm}(kk));
                        if ~isempty(ix)
                            t1{mm} = (B(ix,:) + C(ix,:)*A) * O.Y{mm}';
                        else
                            t1{mm} = zeros(0,O.C(mm));
                        end
                        tot = tot + O.d_k{mm}(kk);
                    end

                  for mm in O.M:
                gJ{mm}(logical(O.S{mm}(kk,:)'),:) = ...
                            gJ{mm}(logical(O.S{mm}(kk,:)'),:) + t1{mm};


    JC = JC/2;

    #%clear A B C t1 z_k y_sub %cc d_k D

    #% Constants %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    fc = .5*( log(pi) )*sum(O.d(O.nes)) - .5*sum(( log(O.N-1)+log(O.a(O.nes)) ).*O.d(O.nes)) ...
        + sum(gammaln(O.nu(O.nes))) - sum(gammaln(.5*O.d(O.nes))) ...
        - sum(O.nu(O.nes).*log(O.lambda(O.nes))) - sum(log(O.beta(O.nes)));

    #% 3rd TERM %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #% Proxy of log abs det W %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if nargout > 1:
        for mm in O.M:
            [rr, cc] = size(O.W{mm});
            if rr == cc:
                [t1, D] = eig(O.W{mm}*O.W{mm}');
                D = diag(D);
                JD = JD - sum(log(abs(sqrt(D))));
                        gJ{mm} = (gJ{mm} - eye(size(gJ{mm})))*O.W{mm};
            else:
                [t1, D] = eig(O.W{mm}*O.W{mm}');
                D = diag(D);
                JD = JD - sum(log(abs(sqrt(D))));
                        gJ{mm} = (gJ{mm} - eye(size(gJ{mm})))*O.W{mm};
    #%             clear t1 D
    else:
        for mm in O.M:
            [rr, cc] = size(O.W{mm});
            if rr == cc:
                D = eig(O.W{mm}*O.W{mm}');
                JD = JD - sum(log(abs(sqrt(D))));
            else:
                D = eig(O.W{mm}*O.W{mm}');
                JD = JD - sum(log(abs(sqrt(D))));
    #%             clear D

    J = JE + JF + JC + JD + fc;
                        '''