"""
fork from python-rl and pybrain for visualization
"""
#import numpy as np
import autograd.numpy as np
from matplotlib.pyplot import ion, draw, Rectangle, Line2D
import matplotlib.pyplot as plt

# If theta  has gone past our conceptual limits of [-pi,pi]
# map it onto the equivalent angle that is in the accepted range (by adding or subtracting 2pi)
     
def remap_angle(theta):
    return _remap_angle(theta)
    
def _remap_angle(theta):
    while theta < -np.pi:
        theta += 2. * np.pi
    while theta > np.pi:
        theta -= 2. * np.pi
    return theta
    

## loss function given a state vector. the elements of the state vector are
## [cart location, cart velocity, pole angle, pole angular velocity]


def loss(state, alpha=[1,1,0.5,0.5]):
    return _loss(state, alpha)

class CartPole:
    """Cart Pole environment. This implementation allows multiple poles,
    noisy action, and random starts. It has been checked repeatedly for
    'correctness', specifically the direction of gravity. Some implementations of
    cart pole on the internet have the gravity constant inverted. The way to check is to
    limit the force to be zero, start from a valid random start state and watch how long
    it takes for the pole to fall. If the pole falls almost immediately, you're all set. If it takes
    tens or hundreds of steps then you have gravity inverted. It will tend to still fall because
    of round off errors that cause the oscillations to grow until it eventually falls.
    """

    def __init__(self, visual=False):
        self.cart_location = 0.0
        self.cart_velocity = 0.0
        self.pole_angle = np.pi    # angle is defined to be zero when the pole is upright, pi when hanging vertically down
        self.pole_velocity = 0.0
        self.visual = visual

        # Setup pole lengths and masses based on scale of each pole
        # (Papers using multi-poles tend to have them either same lengths/masses
        #   or they vary by some scalar from the other poles)
        self.pole_length = 0.5 
        self.pole_mass = 0.5 

        self.mu_c = 0.001 #   # friction coefficient of the cart
        self.mu_p = 0.001 # # friction coefficient of the pole
        self.sim_steps = 50         # number of Euler integration steps to perform in one go
        self.delta_time = 0.05       # time step of the Euler integrator
        self.max_force = 20.
        self.gravity = 9.8
        self.cart_mass = 0.5

        # for plotting
        self.cartwidth = 1.0
        self.cartheight = 0.2

        if self.visual:
            self.drawPlot()

    def setState(self, state):
        self.cart_location = state[0]
        self.cart_velocity = state[1]
        self.pole_angle = state[2]
        self.pole_velocity = state[3]
            
    def getState(self):
        return np.array([self.cart_location,self.cart_velocity,self.pole_angle,self.pole_velocity])

    # reset the state vector to the initial state (down-hanging pole)
    def reset(self):
        self.cart_location = 0.0
        self.cart_velocity = 0.0
        self.pole_angle = np.pi
        self.pole_velocity = 0.0

    # This is where the equations of motion are implemented
    def performAction(self, action = 0.0):
        # prevent the force from being too large
        force = self.max_force * np.tanh(action/self.max_force)

        # integrate forward the equations of motion using the Euler method
        for step in range(self.sim_steps):
            s = np.sin(self.pole_angle)
            c = np.cos(self.pole_angle)
            m = 4.0*(self.cart_mass+self.pole_mass)-3.0*self.pole_mass*(c**2)
            
            cart_accel = (2.0*(self.pole_length*self.pole_mass*(self.pole_velocity**2)*s+force-self.mu_c*self.cart_velocity)\
                -3.0*self.pole_mass*self.gravity*c*s )/m
            
            pole_accel = (-3.0*c*(self.pole_length/2.0*self.pole_mass*(self.pole_velocity**2)*s + force-self.mu_c*self.cart_velocity)+\
                6.0*(self.cart_mass+self.pole_mass)/(self.pole_mass*self.pole_length)*\
                (self.pole_mass*self.gravity*s - 2.0/self.pole_length*self.mu_p*self.pole_velocity) \
                )/m

            # Update state variables
            dt = (self.delta_time / float(self.sim_steps))
            # Do the updates in this order, so that we get semi-implicit Euler that is simplectic rather than forward-Euler which is not. 
            self.cart_velocity += dt * cart_accel
            self.pole_velocity += dt * pole_accel
            self.pole_angle    += dt * self.pole_velocity
            self.cart_location += dt * self.cart_velocity

        if self.visual:
            self._render()

    # remapping as a member function
    def remap_angle(self):
        self.pole_angle = _remap_angle(self.pole_angle)
    
    # the loss function that the policy will try to optimise (lower) as a member function
    def loss(self):
        return _loss(self.getState())
    
    def terminate(self):
        """Indicates whether or not the episode should terminate.

        Returns:
            A boolean, true indicating the end of an episode and false indicating the episode should continue.
            False is returned if either the cart location or
            the pole angle is beyond the allowed range.
        """
        return np.abs(self.cart_location) > self.state_range[0, 1] or \
               (np.abs(self.pole_angle) > self.state_range[2, 1]).any()

   # the following are graphics routines
    def drawPlot(self):
        ion()
        self.fig = plt.figure()
        # draw cart
        self.axes = self.fig.add_subplot(111, aspect='equal')
        self.box = Rectangle(xy=(self.cart_location - self.cartwidth / 2.0, -self.cartheight), 
                             width=self.cartwidth, height=self.cartheight)
        self.axes.add_artist(self.box)
        self.box.set_clip_box(self.axes.bbox)

        # draw pole
        self.pole = Line2D([self.cart_location, self.cart_location + np.sin(self.pole_angle)], 
                           [0, np.cos(self.pole_angle)], linewidth=3, color='black')
        self.axes.add_artist(self.pole)
        self.pole.set_clip_box(self.axes.bbox)

        # set axes limits
        self.axes.set_xlim(-10, 10)
        self.axes.set_ylim(-0.5, 2)
        


    def _render(self):
        self.box.set_x(self.cart_location - self.cartwidth / 2.0)
        self.pole.set_xdata([self.cart_location, self.cart_location + np.sin(self.pole_angle)])
        self.pole.set_ydata([0, np.cos(self.pole_angle)])
        self.fig.show()
        
        plt.pause(0.2)



def move_cart(initial_x, steps=1, visual=False, display_plots=True, remap_angle=False, noisy_dynamics=False, **kwargs):
    """

    Parameters
    ----------
    initial_x : list-like
        [cart_location, cart_velocity, pole_angle, pole_velocity, action]
    steps: int
        number of steps taken
    visual: bool
        whether to show image of cart state
    display_plots: bool
        
    remap_angle: bool
        whether to remap angle to between pi -pi
    noisy_dynamics: bool
        whether to introduce noise to the dynamics
    noise_function: function
        the function that applies noise to array
    var: float
        the variance for the noise function
        
    Returns
    -------
    list 
        x_history of state at discrete intervals
    """
    assert steps != 4, "Sorry, I don't like 4 steps"
    if noisy_dynamics: 
        try:
            kwargs['noise_function'] 
        except:
            raise AttributeError('no noise_function given but you asked for noisy dynamics')
    
    cp = CartPole(visual=visual)
    x_ = initial_x.copy()
    if noisy_dynamics: x_ = kwargs['noise_function'](x_, var=kwargs['var'])
    cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action = x_
    

    for _ in range(steps):
        if visual: cp.drawPlot()
        cp.performAction(action)
        if remap_angle: cp.remap_angle()
        if noisy_dynamics: 
            cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action = kwargs['noise_function']([cp.cart_location, cp.cart_velocity, cp.pole_angle, 
                                                                                                                    cp.pole_velocity, action], var=kwargs['var'])
        try: 
            x_history = np.vstack((x_history, np.array([cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action])))
        except:
            x_history = np.array((initial_x, [cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action]))
        
    t = range(x_history.shape[0]) if steps > 1 else 1
    
    if display_plots and steps > 1:
        fig, axs = plt.subplots(1, 3, figsize=(20, 5))
        
        axs[0].plot(t, [x[0] for x in x_history], label='cart_location')
        axs[0].plot(t, [x[1] for x in x_history], label='cart_velocity')
        axs[0].plot(t, [x[2] for x in x_history], label='pole_angle')
        axs[0].plot(t, [x[3] for x in x_history], label='pole_velocity')
        axs[0].legend()
        
        axs[1].plot([x[0] for x in x_history], [x[1] for x in x_history])
        axs[1].set_xlabel('cart_location')
        axs[1].set_ylabel('cart_velocity')
        
        axs[2].plot([x[2] for x in x_history], [x[3] for x in x_history])
        axs[2].set_xlabel('pole_angle')
        axs[2].set_ylabel('pole_velocity')
        
        fig.suptitle('action: {}'.format(action))
        fig.tight_layout()
    
    elif display_plots and steps == 1: print("You're trying to plot over {} steps, which is not plottable, pick a number greater than 1".format(steps))
        
    if len(x_history) != 5: return x_history[-1]
    else: return x_history

def generate_data(n, steps=1, train_proportion=0.8, remap_angle=False):
    for i in range(n):
        try:
            x_ = np.array([np.random.normal(), np.random.uniform(-10, 10), np.random.uniform(-np.pi,np.pi), np.random.uniform(-15,15), np.random.uniform(-20,20)])
            y_ = np.array(move_cart(x_, steps=steps, display_plots=False, remap_angle=remap_angle)) - x_
            x = np.vstack((x, x_))
            y = np.vstack((y, y_))

        except:
            x = np.array([np.random.normal(), np.random.uniform(-10, 10), np.random.uniform(-np.pi,np.pi), np.random.uniform(-15,15), np.random.uniform(-20,20)])
            y = np.array(move_cart(x, steps=steps, display_plots=False, remap_angle=remap_angle)) - x
        
    x_train, y_train, x_test, y_test = x[:int(n*train_proportion)], y[:int(n*train_proportion)], x[int(n*train_proportion):], y[int(n*train_proportion):]

    return x_train, y_train, x_test, y_test

def plot_y_contour_as_difference_in_x(initial_x, index_pair, range_x_pair, index_to_variable, dynamics='actual', model=None, **kwargs):
    '''
    function for plotting y contours when y is modelled 
    as X(T) - X(0) and 2 variables are scanned across 
    
    Parameters
    ----------
    index_pair : list-like of int
        Which index pair of X (or variables) to scan over
    range_x_pair : list-like of list-like
        Scan range of both variables
    '''
   
    index_1, index_2 = index_pair
    range_1, range_2 = range_x_pair
    
    x_0_grid = np.zeros((len(range_1),len(range_2),5))
    x_t_grid = np.zeros((len(range_1),len(range_2),5))
    
    for i,value_1 in enumerate(range_1):
        for j, value_2 in enumerate(range_2):
            x = initial_x.copy()
            x[index_1] = value_1
            x[index_2] = value_2
            x_0_grid[i,j] = x
            if dynamics == 'actual': x_t_grid[i,j] = np.array(move_cart(x, steps=1, display_plots=False, remap_angle=False))
            elif dynamics == 'predicted':
                assert model, 'no model given'
                x_t_grid[i,j] = model(x, kwargs['alpha'], kwargs['X_i_vals'], kwargs['sigma']) # TODO make this model.predict()
    y_grid = x_t_grid - x_0_grid
    y_grid = np.moveaxis(y_grid, -1, 0)   
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    
    if index_pair == [2,3]:
        vmin = None
        vmax = None
    else:
        vmin = y_grid.min()
        vmax = y_grid.max()
    axs[0,0].contourf(range_1, range_2, y_grid[0].T, vmin=vmin, vmax=vmax)
    axs[0,0].set_title('cart_location')
    axs[0,0].set_xlabel('{} initial value'.format(index_to_variable[index_1]))
    axs[0,0].set_ylabel('{} initial value'.format(index_to_variable[index_2]))    
    axs[0,1].contourf(range_1, range_2, y_grid[1].T, vmin=vmin, vmax=vmax)
    axs[0,1].set_title('cart_velocity')
    axs[0,1].set_xlabel('{} initial value'.format(index_to_variable[index_1]))
    axs[0,1].set_ylabel('{} initial value'.format(index_to_variable[index_2]))
    axs[1,0].contourf(range_1, range_2, y_grid[2].T, vmin=vmin, vmax=vmax)
    axs[1,0].set_title('pole_angle')
    axs[1,0].set_xlabel('{} initial value'.format(index_to_variable[index_1]))
    axs[1,0].set_ylabel('{} initial value'.format(index_to_variable[index_2]))
    axs[1,1].contourf(range_1, range_2, y_grid[3].T, vmin=vmin, vmax=vmax)
    axs[1,1].set_title('pole_velocity')
    axs[1,1].set_xlabel('{} initial value'.format(index_to_variable[index_1]))
    axs[1,1].set_ylabel('{} initial value'.format(index_to_variable[index_2]))
    
    if 4 not in index_pair: fig.suptitle('action: {}'.format(initial_x[-1]))
    fig.tight_layout()

def range_x_pair_finder(index_pair, x_range_for_index):
    range_x_pair = []
    for index in index_pair:
        range_x_pair.append(x_range_for_index[index])
    return np.array(range_x_pair)

def project_x_using_model(initial_x, model, steps, remap_angle=False, compound_predictions=False, **kwargs):
    
    cp = CartPole()
    cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action = initial_x
    pred_ = None
    
    for step in range(steps):
        x_ = np.array([cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action])
        cp.performAction(action)
        if remap_angle: cp.remap_angle()
        y_ = np.array([cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action])
        if pred_ is not None: 
            if compound_predictions:
                pred_ = pred_ + model(pred_, kwargs['alpha'], kwargs['X_i_vals'], kwargs['sigma']) #TODO change to model.predict
            else:
                pred_ = x_ + model(x_, kwargs['alpha'], kwargs['X_i_vals'], kwargs['sigma']) #TODO change to model.predict
          
        try:
            prediction_history = np.vstack((prediction_history, pred_))
            y_history = np.vstack((y_history, y_))
        except:
            assert all(x_) == all(initial_x), '{}_______{}'.format(x_, initial_x)
            pred_ = x_ + model(x_, kwargs['alpha'], kwargs['X_i_vals'], kwargs['sigma'])
            prediction_history = np.vstack((x_, pred_))
            y_history = np.vstack((x_, y_))
        print('action in project_x_using_model step {} was {}'.format(step, action))
    
    return prediction_history, y_history

def plot_prediction_vs_actual_over_time(prediction_history, y_history, title=None):
    
    t = range(len(prediction_history))
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    axs[0,0].plot(t, [y[0] for y in y_history], label='actual values')
    axs[0,0].plot(t, [pred[0] for pred in prediction_history], label='predicted values')
    axs[0,0].set_ylabel('Y_cart_location')
    axs[0,0].set_xlabel('time_step')    
    axs[0,1].plot(t, [y[1] for y in y_history], label='actual values')
    axs[0,1].plot(t, [pred[1] for pred in prediction_history], label='predicted values')
    axs[0,1].set_ylabel('Y_cart_velocity')
    axs[0,1].set_xlabel('time_step')    
    axs[1,0].plot(t, [y[2] for y in y_history], label='actual values')
    axs[1,0].plot(t, [pred[2] for pred in prediction_history], label='predicted values')
    axs[1,0].set_ylabel('Y_pole_angle')
    axs[1,0].set_xlabel('time_step')
    axs[1,1].plot(t, [y[3] for y in y_history], label='actual values')
    axs[1,1].plot(t, [pred[3] for pred in prediction_history], label='predicted values')
    axs[1,1].set_ylabel('Y_pole_velocity')
    axs[1,1].set_xlabel('time_step')
    axs[0,1].legend(loc='upper right')
    if title: descriptive_title = title
    else: descriptive_title = ''

    fig.suptitle(descriptive_title + ' action: {}'.format(y_history[0][-1]))
    fig.tight_layout()
    


def plot_y_scans(initial_x, index_to_variable, x_range_for_index, model=None, remap_angle=False, **kwargs):
    '''
    function for plotting y values when y is modelled 
    as X(T) - X(0)
    
    Parameters
    ----------
    model : 
        linear regression model
    '''
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))

    for index in range(4):
        
        range_x = x_range_for_index[index]
        
        x = initial_x.copy()
        y_results = []
        x_0 = None
        x_t = None

        for i in range_x:
            x[index] = i
            x_t = np.array(move_cart(x, steps=1, display_plots=False, remap_angle=remap_angle))
            try:
                x_t_results = np.vstack((x_t_results, x_t))
                x_0 = np.vstack((x_0, x))
            except:
                x_t_results = x_t
                x_0 = x.copy()

        if model: 
            try: 
                predictions = model(x_0, kwargs['alpha'], kwargs['X_i_vals'], kwargs['sigma']) # TODO change to model.predict
            except:
                predictions = model.predict(x_0) #linear model

        y_results = x_t_results - x_0
        if remap_angle: y_results[:,2] = np.array([_remap_angle(theta) for theta in y_results[:,2]])
        
        axs[int(round((index+1)/4,0)),index%2].plot(range_x, [y[0] for y in y_results], 'C0-', label='c_l')
        axs[int(round((index+1)/4,0)),index%2].plot(range_x, [y[1] for y in y_results], 'C1-', label='c_v')
        axs[int(round((index+1)/4,0)),index%2].plot(range_x, [y[2] for y in y_results], 'C2-', label='p_a')
        axs[int(round((index+1)/4,0)),index%2].plot(range_x, [y[3] for y in y_results], 'C3-', label='p_v')
        if model:
            axs[int(round((index+1)/4,0)),index%2].plot(range_x, [pred_[0] for pred_ in predictions], 'C0--', label='c_l_pred')
            axs[int(round((index+1)/4,0)),index%2].plot(range_x, [pred_[1] for pred_ in predictions], 'C1--', label='c_v_pred')
            axs[int(round((index+1)/4,0)),index%2].plot(range_x, [pred_[2] for pred_ in predictions], 'C2--', label='p_a_pred')
            axs[int(round((index+1)/4,0)),index%2].plot(range_x, [pred_[3] for pred_ in predictions], 'C3--', label='p_v_pred')
        axs[int(round((index+1)/4,0)),index%2].set_ylabel('component of y values')
        axs[int(round((index+1)/4,0)),index%2].set_xlabel('{} initial values'.format(index_to_variable[index]))
        axs[int(round((index+1)/4,0)),index%2].legend()

    fig.suptitle('action: {}'.format(initial_x[-1]))
    fig.tight_layout()

def kernel(X, X_dash, sigma):

    if type(X) == list: X = np.array(X)
    if type(X_dash) == list: X_dash = np.array([X_dash])
    
    try:
        squared_numerator = np.array([(X[i]-X_dash[i])**2 if i != 2  else (np.sin((X[i]-X_dash[i])/2))**2 for i in range(5)])
    except:
        print(X, X_dash, '<------------ fix this')
    return np.exp(-np.sum(np.divide(squared_numerator, 2*np.square(sigma))))

def generate_K(X, M, sigma, kernel=kernel):
    if type(M) != list: M = np.array(M)
        
    for x_location in X:
        K_row = np.array([kernel(x_location, RBF_x, sigma) for RBF_x in X[M]])
        try:
            KnM = np.vstack((KnM, K_row))
        except:
#             print('first row of K: {} <---------------------- this should only happen once'.format(K_row.shape))
            KnM = K_row
            
    return KnM

def train_alpha(x_train, y_train, no_RBC, sigma, n, train_proportion, kernel=kernel, lam=0.00001):
    
    M_vals = np.random.randint(0, high=n*train_proportion, size=no_RBC)
    X_i_vals = x_train[M_vals]
    KnM_ = generate_K(x_train, M_vals, sigma, kernel)
    KMM_ = generate_K(X_i_vals, [i for i in range(M_vals.size)], sigma, kernel)
    alpha = np.linalg.lstsq(np.matmul(KnM_.T, KnM_) + lam*KMM_, np.matmul(KnM_.T, y_train))[0]

#     alpha = np.linalg.lstsq(np.matmul(KnM_.T, KnM_), np.matmul(KnM_.T, y_train))[0]
#     alpha = np.matmul(np.linalg.pinv(KnM_), y_train).T
#     print('alpha.shape: {}'.format(alpha.shape))
    
    return alpha, X_i_vals

def predict(x_test, alpha, X_i_vals, sigma, kernel=kernel):
    KnM_test= [None, None]
    for X_i in X_i_vals:
        if x_test.size > 4:
            assert x_test.size % 5 == 0, 'x_test.size: ' + str(x_test.size)
            
            if x_test.ndim == 1:
                KnM_test_row = kernel(X_i, x_test, sigma=sigma)
            else:
                KnM_test_row = np.array([kernel(X_i, x_test_, sigma=sigma) for x_test_ in x_test])
            
        elif x_test.size == 4:
            if x_test.ndim > 1: x_test = x_test[0]
            KnM_test_row = kernel(X_i, x_test, sigma=sigma)
        try:
            KnM_test = np.vstack((KnM_test, KnM_test_row))
        except:
            KnM_test = KnM_test_row
    predictions = np.matmul(KnM_test.T, alpha)
    
    return predictions

def display_RMSE(predictions, y_test):
    targets = y_test            
    return [np.sqrt(np.mean((predictions[:,j]-targets[:,j])**2)) for j in range(4)] 

def project_loss(initial_x, steps=1):
    cp = CartPole()
    cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action = initial_x
    loss_history = [loss(initial_x[:-1])]
    y_history = np.array([initial_x])
    
    for _ in range(steps):
        cp.performAction(action)
        cp.remap_angle()
        y_ = np.array([cp.cart_location, cp.cart_velocity, cp.pole_angle, cp.pole_velocity, action])
        loss_ = loss(y_[:-1])
        loss_history.append(loss_)
        y_history = np.vstack((y_history, y_))
        
    return np.array(loss_history), y_history

def plot_loss_contours(initial_x, initial_p, index_pair, range_p_pair):
    index_1, index_2 = index_pair
    range_1, range_2 = range_p_pair
    loss_grid = np.zeros((len(range_1),len(range_2)))
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    for i,value_1 in enumerate(range_1):
        for j, value_2 in enumerate(range_2):
            x_ = initial_x.copy()
            p_ = initial_p.copy()
            p_[index_1] = value_1
            p_[index_2] = value_2
            x_[-1] = 20 * np.tanh(np.dot(x_[:-1],p_))
            y_ = np.array(move_cart(x_, steps=1, display_plots=False, remap_angle=False))
            loss_y = loss(y_)
            loss_x = loss(initial_x.copy())
#             print(loss_y,loss_x,y_,x_)
            loss_grid[i,j] = loss_y - loss_x
                
    plt.contourf(range_1, range_2, loss_grid.T)
    cs = ax.contourf(range_1, range_2, loss_grid.T)
    fig.colorbar(cs, ax=ax)
    plt.title('change in loss function')
    plt.xlabel('$p_{}$ value'.format(index_1))
    plt.ylabel('$p_{}$ value'.format(index_2)) 
    print(np.max(loss_grid))

def policy_exponent(X, X_i, W):
    if X.size == 5: X = X[:-1]
    if X_i.size == 5: X_i = X_i[:-1]
    diff_ = X - X_i    
    try:
        power_ = -0.5 * np.matmul(np.matmul(diff_, W), diff_.T)
        # print(diff_,power_)
    except: # this solves issue of scipy.optimize.minimize needing 1D array
        W = np.reshape(W, (-1, 4))
        power_ = -0.5 * np.matmul(np.matmul(diff_, W), diff_.T)
        # TODO assert W is symmetric
    # print('#####',np.matmul(diff_.T, W), diff_)
    return np.exp(power_)

def non_linear_policy(w_i, X, X_i_vals, W):
    # print('--',np.sum(np.array([w_i[i] * policy_exponent(X, X_i_vals[i], W) for i in range(int(w_i.size/4))])))
    return np.sum(np.array([w_i[i] * policy_exponent(X, X_i_vals[i], W) for i in range(int(w_i.size))])) #TODO vectorise this 

def _loss(state, sig_):
    # alpha = np.array([5,2,0.7,3])
    # return sum(1 - 1/(np.exp(np.abs(np.array(state)/alpha))))

    # return sum([1 - 1/(np.exp((state[i]/alpha[i])**2)) for i in range(4)])
   
    if type(state) == list: state = np.array(state).flatten()
    state = state[:4]
    # print(state)
    loss_ = 1-np.exp(-np.dot(state/sig_,state/sig_)/(2.0))
    # print(np.round(loss_,5))
    return loss_

def loss_after_steps(x_row, kwargs_, steps=30):
    cumulative_loss = 0
    if type(x_row) == list: x_row = np.array(x_row)
    x_ = x_row.copy().flatten()
    x_[2] = remap_angle(x_[2])
    if kwargs_['linear']:
        sig_list = kwargs_['sig']*steps
    else:
        sig_list = np.linspace(kwargs_['sig_start'], kwargs_['sig_end'], steps)
    
    for sig_ in sig_list: #for step in range(steps)
        if kwargs_['linear']: action_ = 20 * np.tanh(np.dot(kwargs_['p'], np.array(x_).flatten()[:-1])/20)
        
        else: 
            if kwargs_['parameter_to_be_optimised'] == 'entire_array':
                ris = -kwargs_['no_RBC']*4 #radial_index_start
                w_i = kwargs_[kwargs_['parameter_to_be_optimised']][:ris-16]
                flat_W = kwargs_[kwargs_['parameter_to_be_optimised']][ris-16:ris]
                X_i_vals = kwargs_[kwargs_['parameter_to_be_optimised']][ris:]
                W_ = flat_W.reshape(4,4)
                W = np.matmul(W_.T,W_)
                kwargs_['w_i'] = w_i
                kwargs_['W'] = W
                kwargs_['X_i_vals'] = X_i_vals
            action_ = non_linear_policy(kwargs_['w_i'], x_[:-1], kwargs_['X_i_vals'], kwargs_['W']) 
        x_[-1] = action_

        if kwargs_['model_predictive_control']:
            y_ = kwargs_['rollout_prediction_model'](x_, kwargs_['rollout_prediction_model_attr']['alpha'], 
                                                        kwargs_['rollout_prediction_model_attr']['X_i_vals'], 
                                                        kwargs_['rollout_prediction_model_attr']['sigma']) 
            y_ = np.array(y_)
            #change to model.predict
        else:
            y_ = np.array(move_cart(x_, steps=1, display_plots=False, remap_angle=True)) 
        
        # if kwargs_['parameter_to_be_optimised'] == 'alpha':
        cumulative_loss += loss(y_.flatten(), sig_) 
        x_ = y_.copy()
        # else:
            # return loss(y_.flatten())
    # if not kwargs_['linear']:
    #     fi = open("loss_.txt", "a")
    #     fi.write(str(cumulative_loss)+',')
    #     fi.close()

    print('cumulative_loss: \t', np.round(cumulative_loss,4))
    return cumulative_loss


def training_loss(array_for_optimisation, x_train, kwargs_):   
    # array_for_optimisation is [w_i vector, flattened W matrix]
    kwargs_[kwargs_['parameter_to_be_optimised']] = array_for_optimisation    
    print(array_for_optimisation)
    # print(parameter_to_be_optimised[0])
    # return sum(np.apply_along_axis(loss_after_action_step, 1, x_train, kwargs_))
    # try:
    loss_ = loss_after_steps(x_train, kwargs_)
    print(loss_)
    return loss_
    # except:
    #     loss_ = sum(np.apply_along_axis(loss_after_steps, 1, x_train, kwargs_))
    #     print(loss_, array_for_optimisation)
    #     return loss_


def add_noise(data_array, var=0.01):#, lam=0.05 , var=[10,20,2*np.pi,30,40]):
    if type(data_array) == list: data_array = np.array(data_array)  
#     if type(var) == list: var = np.array(var)  
#     if var is None: var = (np.std(data_array, axis=0)*lam)**2
    if data_array.shape == data_array.size: data_array = np.expand_dims(data_array,0) 
    
#     for i in range(var.size):
#         noise = np.random.normal(0,var[i], (int(data_array.size/var.size)))
#         print(noise, var[i])
#         noisy_array_column = data_array[:,i] + noise
#         try:
#             noisy_array = np.vstack((noisy_array, noisy_array_column))
#         except:
#             print('----------------')
#             noisy_array = noisy_array_column
    noisy_array = np.random.normal(0,var,(data_array.shape)) + data_array
    return noisy_array

def plot_predictions_vs_actual(predictions, actual, index_to_variable):
    fig,axs = plt.subplots(2,2,figsize=(12,9))
    for j in range(4):
        ul = max(max(predictions[:,j]), max(actual[:,j]))
        ll = min(min(predictions[:,j]), min(actual[:,j]))
        axs[int(round((j+1)/4,0)),j%2].scatter(predictions[:,j], actual[:,j])
        axs[int(round((j+1)/4,0)),j%2].plot([ll,ul],[ll,ul], color='g')
        axs[int(round((j+1)/4,0)),j%2].set_title(index_to_variable[j])
        axs[int(round((j+1)/4,0)),j%2].set_xlabel('prediction')
        axs[int(round((j+1)/4,0)),j%2].set_ylabel('actual')

        fig.tight_layout()