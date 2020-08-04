from collections import OrderedDict
import pandas as pd
import numpy as np
from datetime import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import dates
import json
from datetime import timedelta

### CONSTANTS

ACCOUNT_COLORS = OrderedDict()
ACCOUNT_COLORS["Left"] = "#2c7bb6"
ACCOUNT_COLORS["thenation"] = "#2c7bb6"
ACCOUNT_COLORS["bot1"] = "#08519c"
ACCOUNT_COLORS["bot2"] = "#2171b5"
ACCOUNT_COLORS["bot3"] = "#4292c6"
ACCOUNT_COLORS["Center-left"] = "#abd9e9"
ACCOUNT_COLORS["washingtonpost"] = "#abd9e9"
ACCOUNT_COLORS["bot4"] = "#9ecae1"
ACCOUNT_COLORS["bot5"] = "#c6dbef"
ACCOUNT_COLORS["bot6"] = "#deebf7"
ACCOUNT_COLORS["Center"] = "0.8"
ACCOUNT_COLORS["USATODAY"] = "0.8"
ACCOUNT_COLORS["bot7"] = "0.5"
ACCOUNT_COLORS["bot9"] = "0.4"
ACCOUNT_COLORS["bot8"] = "0.6"
ACCOUNT_COLORS["Center-right"] = "#f4a582"
ACCOUNT_COLORS["WSJ"] = "#f4a582"
ACCOUNT_COLORS["bot12"] = "#fc9272"
ACCOUNT_COLORS["bot11"] = "#fcbba1"
ACCOUNT_COLORS["bot10"] = "#fee0d2"
ACCOUNT_COLORS["Right"] = "#d7191c"
ACCOUNT_COLORS["BreitbartNews"] = "#d7191c"
ACCOUNT_COLORS["bot15"] = "#a50f15"
ACCOUNT_COLORS["bot14"] = "#cb181d"
ACCOUNT_COLORS["bot13"] = "#ef3b2c"

INIT_SEED_RENAME = OrderedDict()
INIT_SEED_RENAME['thenation'] = 'Left'
INIT_SEED_RENAME['washingtonpost'] = 'Center-left'
INIT_SEED_RENAME['USATODAY'] = 'Center'
INIT_SEED_RENAME['WSJ'] = 'Center-right'
INIT_SEED_RENAME['BreitbartNews'] = 'Right'

SEED_TWITTER_ID = {
  'USATODAY':'15754281',
  'thenation':'1947301',
  'washingtonpost':'2467791',
  'WSJ':'3108351',
  'BreitbartNews':'457984599'
}

SEED_NAMES = {v: k for k, v in SEED_TWITTER_ID.items()}

INIT_SEED_MAP = {
    'thenation': ['bot1', 'bot2', 'bot3'],
    'washingtonpost': ['bot4', 'bot5', 'bot6'],
    'USATODAY': ['bot7', 'bot8', 'bot9'],
    'WSJ': ['bot10', 'bot11', 'bot12'],
    'BreitbartNews': ['bot14', 'bot15', 'bot13']
}

BOT_SEED_MAP = {
    'bot1': 'thenation',
    'bot2': 'thenation',
    'bot3': 'thenation',
    'bot4': 'washingtonpost',
    'bot5': 'washingtonpost',
    'bot6': 'washingtonpost',
    'bot7': 'USATODAY',
    'bot8': 'USATODAY',
    'bot9': 'USATODAY',
    'bot10': 'WSJ',
    'bot11': 'WSJ',
    'bot12': 'WSJ',
    'bot13': 'BreitbartNews',
    'bot14': 'BreitbartNews',
    'bot15': 'BreitbartNews',
}

SEED_URL_SCORE = {
  'USATODAY':0.0582,
  'thenation':-0.7298,
  'washingtonpost':-0.2342,
  'WSJ':0.0106,
  'BreitbartNews':0.7419
}

USATODAY_HASHTAG_SCORE = -0.2456

bot_end_date = {'bot13': '2019-11-10', 'bot14': '2019-11-14'}

def plot_bots_and_summary(
    bots_df, 
    y_label = "metric?",
    minor_locator = dates.DayLocator(interval=15),
    minor_formatter = dates.DateFormatter('%d-%b'),
    major_locator = dates.MonthLocator(),
    major_formatter = dates.DateFormatter(''),
    bots_legend_loc = (0.01,1),
    bots_legend_ncol = 5,
    filename="bots_and_summary.pdf",
    sem=False,
    figsize=(8,8),
    ncol_main_plot=5,
    leg_size_main_plot=14,
    confidence_interval=1.96,
    group_legend=None
):
    fig, (ax2,ax) = plt.subplots(2,1,figsize=figsize,sharex=True,sharey=True)
    # ploting seeds
    names = [seed for seed in ACCOUNT_COLORS.keys() if seed in INIT_SEED_MAP.keys()]
    colors = [ACCOUNT_COLORS.get(name) for name in names]
    
    bots_df = bots_df.copy()
    
    if sem:
        bots_df_sem = bots_df.copy()
        
    for seed in INIT_SEED_RENAME.keys():
        cols = INIT_SEED_MAP[seed]
        bots_df[seed] = bots_df[cols].mean(axis=1)
        bots_df[seed].rename(
            INIT_SEED_RENAME[seed]
        ).plot(color=ACCOUNT_COLORS.get(seed), ax=ax,lw=4)
        if sem:
            bots_df_sem[seed] = bots_df[cols].sem(axis=1) * confidence_interval # 1.96 ~ 95% confidence interval
            ax.fill_between(
                bots_df[seed].index.values,
                bots_df[seed] - bots_df_sem[seed],
                bots_df[seed] + bots_df_sem[seed],
                alpha=.2,
                color=ACCOUNT_COLORS.get(seed)
            )

    names = BOT_SEED_MAP.keys()
    colors = [ACCOUNT_COLORS.get(name) for name in names]
    bots_df[list(names)].plot(color=colors, ax=ax2,lw=2)
    ax2.xaxis.set_minor_locator(minor_locator)
    ax2.xaxis.set_minor_formatter(minor_formatter)
    ax2.xaxis.set_major_locator(major_locator)
    ax2.xaxis.set_major_formatter(major_formatter)
    ax.legend(
        prop={'size': leg_size_main_plot},
    #     loc=(1,0),
        frameon=False,
        ncol=ncol_main_plot,
        labels=group_legend
    )
    ax2.legend(
        prop={'size': 9.5},
        loc=bots_legend_loc,
        frameon=False,
        ncol=bots_legend_ncol
    )
    ax.set_ylabel(y_label)
    ax2.set_ylabel(y_label)
    
    #spines
    for a in (ax2,ax):
        a.spines['top'].set_visible(False)
        a.spines['right'].set_visible(False)
        
    plt.xlabel(None)
    plt.tight_layout()
    plt.ylim(0)
    plt.savefig(filename)
    
def calculate_window_scores(accountanalysis,metric,window_size=7, min_periods=3):
    tmp = accountanalysis.loc[
        accountanalysis.index.get_level_values(0).isin(
            ACCOUNT_COLORS.keys()
        )
        & (accountanalysis["{}_ave".format(metric)]!=-200)
    ].stack().reset_index(
        level=[0,1]
    ).loc["{}_ave".format(metric)].groupby(
        ["t_usr_id","timestamp"]
    ).mean().unstack(level=0).droplevel(0,axis=1).rolling(
        window_size, min_periods=min_periods
    ).mean()
        
    return tmp

def plotTwoBarsPlot(bars1, yer1, colors, xticks, bars2=None, yer2=None, figname="plotTwoBarsPlot.pdf", ylabel="Bot score",
                    barWidth = 0.3, label1 = 'Friends', label2 = 'Followers', legend_loc=(.6,.8), ax=None,
                   xlabel_size=16,ylabel_size=16,ylim=0, saveFig=True):
    from matplotlib.patches import Patch

    # The x position of bars
    r1 = np.arange(len(bars1))
    xticks_pos = r1
    
    if not ax:
        fig,ax=plt.subplots()

    ax.bar(r1, bars1, width = barWidth, color = colors, 
            edgecolor = '#ffffff', 
            yerr=yer1, capsize=7, label=label1, hatch="/")

    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    if bars2 is not None:
        r2 = [x + barWidth for x in r1]
        ax.bar(r2, bars2, width = barWidth, color = colors, 
                     edgecolor = '#ffffff', 
                     yerr=yer2, capsize=7, label=label2, hatch="-")
        xticks_pos = (r1+r2)/2
    
        legend_elements = [
            Patch(facecolor='white', edgecolor='k', label=label1, hatch="/"),
            Patch(facecolor='white', edgecolor='k', label=label2, hatch="-"),
        ]
        plt.legend(
            handles=legend_elements,
            frameon=False,
            ncol=1,
            fontsize=14,
            loc=legend_loc #"upper right"
        )

    # general layout
#     plt.xticks(
#         xticks_pos, 
#     #     overall_botscore.columns
#         xticks,
#         size=16,
#     )
    ax.set_xticks(xticks_pos)
    ax.set_xticklabels(
        xticks,
        fontsize=xlabel_size,
    )
    ax.set_ylabel(ylabel, fontsize=ylabel_size)
    ax.set_ylim(ylim)

    plt.tight_layout()
    if saveFig:
        plt.savefig(figname)
    return ax
    

def load_data(medium, loc, center_score=-0.0635, basepath="",
    end_date='2019-12-02', early_end_bot_idx=[13, 14], fillna=True):
    """ Method used to load CSV files and combine them into a single dataframe to plot timeline drifts.
    """
    df = pd.DataFrame(None, columns=['date'])
    df = df.set_index('date')
    for bot, seed in BOT_SEED_MAP.items():
        filename = basepath + '%s_%s_sliced_%s_tl_%s.csv' % (medium, seed, loc, bot)
        tmp_df = pd.read_csv(filename,
                             usecols=['date', '%s_mean' % medium, '%s_var' % medium, '%s_count' % medium],
#                              parse_dates=['date'],
#                              date_parser=lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                            )
        tmp_df["date"] = pd.to_datetime(tmp_df["date"])
        tmp_df['%s_sem' % bot] = np.sqrt(tmp_df['%s_var' % medium].astype('float').divide(tmp_df['%s_count' % medium].astype('float')))
        tmp_df = tmp_df.rename(columns={
            '%s_mean' % medium: bot,
            '%s_var' % medium: '%s_var' % bot,
            '%s_count' % medium: '%s_count' % bot})
        tmp_df = tmp_df.drop_duplicates(subset={'date'}, keep='last')
        tmp_df = tmp_df.set_index('date')
        tmp_df[bot] = tmp_df[bot] - center_score
        df = df.merge(tmp_df, left_index=True, right_index=True, how='outer')
    df = df.sort_index(ascending=True)
    last_index = df.index[-1]
    end_date = dt.strptime(end_date, '%Y-%m-%d')
    if last_index < end_date:
        delta = end_date - last_index
        new_date_lst = []
        for i in range(1, delta.days + 1):
            day = last_index + timedelta(days=i)
            new_date_lst.append(day)
        df_columns = df.columns
        tmp_df = pd.DataFrame(None, index=new_date_lst, columns=df_columns)
        tmp_df.index.name = 'date'
        df = pd.concat([df, tmp_df])
    for bot_idx in range(1, 16):
        if bot_idx in early_end_bot_idx:
            tmp_df = df.loc[ : dt.strptime(bot_end_date['bot'+str(bot_idx)], '%Y-%m-%d')]
        else:
            tmp_df = df
        for stat in ['', '_var', '_count', '_sem']:
            if fillna:
                tmp_df['bot%s%s' % (bot_idx, stat)] = tmp_df['bot%s%s' % (bot_idx, stat)].fillna(method='ffill')
                tmp_df['bot%s%s' % (bot_idx, stat)] = tmp_df['bot%s%s' % (bot_idx, stat)].fillna(method='bfill')
    return df

def load_data_bias(medium, basepath="",
    end_date='2019-12-02', early_end_bot_idx=[13, 14]):
    df = pd.DataFrame(None, columns=['date'])
    df = df.set_index('date')
    for bot, seed in BOT_SEED_MAP.items():
        filename = basepath + '%s_%s_sliced_home_tl_%s.csv' % (medium, seed, bot)
        tmp_df_usr = pd.read_csv(filename,
                             usecols=['date', '%s_mean' % medium, '%s_var' % medium, '%s_count' % medium],
                             parse_dates=['date'],
                             date_parser=lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                                )
        tmp_df_usr["date"] = pd.to_datetime(tmp_df_usr["date"])

        tmp_df_usr = tmp_df_usr.rename(columns={
            '%s_mean' % medium: bot,
            '%s_var' % medium: '%s_var' % bot,
            '%s_count' % medium: '%s_count' % bot})
        tmp_df_usr = tmp_df_usr.drop_duplicates(subset={'date'}, keep='last')
        tmp_df_usr = tmp_df_usr.set_index('date')
        
        filename = basepath + '%s_%s_sliced_friend_usr_tl_%s.csv' % (medium,seed,bot )
        tmp_df = pd.read_csv(filename,
                             usecols=['date', '%s_mean' % medium, '%s_var' % medium, '%s_count' % medium],
                             parse_dates=['date'],
                             date_parser=lambda x: pd.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
                            )
        tmp_df["date"] = pd.to_datetime(tmp_df["date"])
        tmp_df = tmp_df.rename(columns={
            '%s_mean' % medium: bot,
            '%s_var' % medium: '%s_var' % bot,
            '%s_count' % medium: '%s_count' % bot})
        tmp_df = tmp_df.drop_duplicates(subset={'date'}, keep='last')
        tmp_df = tmp_df.set_index('date')
        tmp_df[bot] = tmp_df_usr[bot] - tmp_df[bot]
        # computes var and sem
        
        tmp_df['%s_var' % bot] = (tmp_df['%s_var' % bot] * (tmp_df['%s_count' % bot] - 1) + 
                                tmp_df_usr['%s_var' % bot] * (tmp_df_usr['%s_count' % bot] - 1))/(tmp_df['%s_count' % bot] + tmp_df_usr['%s_count' % bot] - 2.)
        tmp_df['%s_sem' % bot] = tmp_df['%s_var' % bot] * ((1.0/tmp_df_usr['%s_count' % bot]) + (1.0/tmp_df['%s_count' % bot]))
        tmp_df['%s_sem' % bot] = np.sqrt(tmp_df['%s_sem' % bot])
        tmp_df = tmp_df[[bot, '%s_sem' % bot, '%s_var' % bot]]
        tmp_df['%s_count' % bot] = tmp_df_usr['%s_count' % bot]
        df = df.merge(tmp_df, left_index=True, right_index=True, how='outer')
    df = df.sort_index(ascending=True)
    last_index = df.index[-1]
    end_date = dt.strptime(end_date, '%Y-%m-%d')
    if last_index < end_date:
        delta = end_date - last_index
        new_date_lst = []
        for i in range(1, delta.days + 1):
            day = last_index + timedelta(days=i)
            new_date_lst.append(day)
        df_columns = df.columns
        tmp_df = pd.DataFrame(None, index=new_date_lst, columns=df_columns)
        tmp_df.index.name = 'date'
        df = pd.concat([df, tmp_df])
    for bot_idx in range(1, 16):
        if bot_idx in early_end_bot_idx:
            tmp_df = df.loc[ : dt.strptime(bot_end_date['bot'+str(bot_idx)], '%Y-%m-%d')]
        else:
            tmp_df = df
        for stat in ['', '_var', '_count', '_sem']:
            tmp_df['bot%s%s' % (bot_idx, stat)] = tmp_df['bot%s%s' % (bot_idx, stat)].fillna(method='ffill')
    return df

def compute_sum_plot(df, sel_cols):
    tmp_df = df[
        [s for s in sel_cols if s in df.columns] + 
        [s+'_var' for s in sel_cols if s in df.columns] +
        [s+'_count' for s in sel_cols if s in df.columns]]
    last_valid_index = tmp_df.last_valid_index()
    tmp_df = tmp_df[tmp_df.index <= last_valid_index]
    tmp_df['week'] = tmp_df.index
    tmp_df['week'] = tmp_df['week'].dt.quarter
    gp_rst = tmp_df.groupby('week')
    y_values = tmp_df.index
    last_valid_index_for_cols = {}
    for s in sel_cols:
        last_valid_index_for_cols[s] = tmp_df[s].last_valid_index()
        tmp_df[s] = tmp_df[s].fillna(method='ffill')
        tmp_df[s+'_var'] = tmp_df[s+'_var'].fillna(method='ffill')
        tmp_df[s+'_count'] = tmp_df[s+'_count'].fillna(method='ffill')
    
    for s in sel_cols:
        idx = np.searchsorted(
            tmp_df.index, last_valid_index_for_cols[s].to_datetime64())
        next_idx = tmp_df.index[min(idx+1, len(tmp_df)-1)]
        tmp_df.loc[next_idx:, s] = np.nan
        tmp_df.loc[next_idx:, s+'_var'] = np.nan
        tmp_df.loc[next_idx:, s+'_count'] = np.nan
    
    x_axis_val = tmp_df[[s for s in sel_cols]].mean(axis=1, skipna=True)
    rst_series = None
    sum_count = None
    tmp_count = None
    # compute pooled standard error
    for s in sel_cols:
        tmp_rst_series = tmp_df[s + '_var'] * (tmp_df[s+'_count'] - 1)
        if rst_series is None:
            rst_series = tmp_rst_series
            sum_count = tmp_df[s+'_count'] - 1
            tmp_count  = 1 / tmp_df[s+'_count']
        else:
            rst_series = rst_series.add(tmp_rst_series, fill_value=0)
            sum_count = sum_count.add((tmp_df[s+'_count'] - 1), fill_value=0)
            tmp_count = tmp_count.add(1 / tmp_df[s+'_count'], fill_value=0)

    pooled_sde = np.sqrt(rst_series.astype('float').divide((sum_count).astype('float'))) * np.sqrt(tmp_count)
    mask = np.isfinite(x_axis_val)
    x_axis_val = x_axis_val[mask]
    tmp_date = y_values[mask]
    pooled_sde = pooled_sde[mask]
    return x_axis_val, pooled_sde, tmp_date

def plot_vertical_scores_summary(
    home_tl_df, friends_df, bias_df,
    home_tl_df2, friends_df2, bias_df2,
    middle_line_x=0,figsize=(7,4),
    home_tl_xlim=1, friends_xlim=1, bias_xlim=1,
    home_tl_xlim2=1, friends_xlim2=1, bias_xlim2=1,
    filename="to_delete.pdf",
    label_letters=["A","B","C","D","E","F"]
):
    fig, axs = plt.subplots(2,3,figsize=figsize,sharey=True,sharex=False)
    axs = axs.flatten()
    y_values = home_tl_df.index
    handles=[]
    labels=[]
    for (df,summary_xlim), (ax,pos) in zip(
        zip(
            [
                home_tl_df, friends_df, bias_df,
                home_tl_df2, friends_df2, bias_df2
            ], 
            [
                home_tl_xlim, friends_xlim, bias_xlim,
                home_tl_xlim2, friends_xlim2, bias_xlim2
            ]
        ), 
        zip(
            axs,
            label_letters
        )
    ):
        for seed, title in INIT_SEED_RENAME.items():
            # average bots to plot summary
            sel_cols = INIT_SEED_MAP.get(seed)
            x_axis_val, pooled_sde, tmp_date = compute_sum_plot(df, sel_cols)

            handles.append(ax.plot(
                x_axis_val, 
                tmp_date,
                ls="-",lw=2.5,color=ACCOUNT_COLORS.get(seed),label=title.replace("-"," ").title().replace("Center ","C.")
            )[0])
            labels.append(title)
            if pooled_sde is not None:
                ax.fill_betweenx(
                    tmp_date,
                    x_axis_val - pooled_sde, x_axis_val + pooled_sde,
                    color=ACCOUNT_COLORS.get(seed),
                    alpha=0.3)
            ax.axvline(middle_line_x,ls="--",color="k",lw=.9)
            ax.set_xlim((-1*summary_xlim,summary_xlim))
            ax.text(
                .05,.9,pos,transform=ax.transAxes
            )
    axs[0].yaxis.set_major_locator(dates.MonthLocator())
    axs[0].yaxis.set_major_formatter(dates.DateFormatter('%b-%Y'))
    lgnd= axs[2].legend(
        loc=(1.02,.0),
        frameon=False,
        fontsize=16,
    )
    for i in range(6):
        axs[i].set_xticks([-.5,0,.5])
        axs[i].set_xticklabels([-.5,0,.5])
    
    axs[3].set_xlabel(r"$s_h$")
    axs[4].set_xlabel(r"$s_u$")
    axs[5].set_xlabel(r"$s_h-s_f$");
    plt.tight_layout()
    plt.savefig(filename, bbox_extra_artists=(lgnd,), bbox_inches='tight')
    return axs


def plot_vertical_scores(df,xlabel,filename,xlim=[-1,1],summary_xlim=[-0.5, 0.5],
                         middle_line_x=0,
                         left_line_x=-.5,
                         right_line_x=.5, compute_sum_plot=compute_sum_plot):
    fig, axs = plt.subplots(1,6,figsize=(14,4),sharey=True,sharex=True)
    y_values = df.index
    handles=[]
    labels=[]
    for ax, (seed, title) in zip(axs, INIT_SEED_RENAME.items()):
        # average bots to plot summary
        sel_cols = INIT_SEED_MAP.get(seed)
        x_axis_val, pooled_sde, tmp_date = compute_sum_plot(df, sel_cols)
        
        handles.append(axs[-1].plot(
            x_axis_val, 
            tmp_date,
            ls="-",lw=2.5,color=ACCOUNT_COLORS.get(seed),label=title
        )[0])
        labels.append(title)
        #"""
        if pooled_sde is not None:
            axs[-1].fill_betweenx(
                tmp_date,
                x_axis_val - pooled_sde, x_axis_val + pooled_sde,
                color=ACCOUNT_COLORS.get(seed),
                alpha=0.3)
        #"""
        axs[-1].axvline(middle_line_x,ls="--",color="k",lw=.9)
        # plot reference seed if available
        if seed in df.columns:
            handles.append(ax.plot(df[seed], y_values,ls="--",lw=2,color=ACCOUNT_COLORS.get(seed),label=seed)[0])
            labels.append(seed)
        # plot each bot in their spectrum group
        for col in sel_cols:
            if col in df.columns:
                mean_val = df[col]
                mask = np.isfinite(mean_val)
                mean_val = mean_val[mask]
                tmp_date  = y_values[mask]
                sems = df['{}_sem'.format(col)][mask]

                handles.append(ax.plot(mean_val, tmp_date,ls="-",lw=2.5,color=ACCOUNT_COLORS.get(col),label=col)[0])
                labels.append(col)
                lowerbound = mean_val - sems
                upperbound = mean_val + sems
                ax.fill_betweenx(
                    tmp_date,
                    lowerbound, upperbound,
                    color=ACCOUNT_COLORS.get(col),
                    alpha=0.15)

        ax.set_title(title)
        ax.set_xlim(xlim)
        axs[-1].set_xlim(summary_xlim)
        ax.axvline(middle_line_x,ls="--",color="k",lw=.9)
        ax.axvline(left_line_x,ls="--",color="0.5",lw=.7)
        ax.axvline(right_line_x,ls="--",color="0.5",lw=.7)
#         ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(which="major",axis="y",lw=.5)
        ax.set_xticks([left_line_x,middle_line_x,right_line_x])
        ax.set_xticklabels([str(left_line_x),str(middle_line_x),str(right_line_x)])
        
        # remove the thick little line
        for tic in ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
            
#     axs[0].yaxis.set_minor_locator(dates.DayLocator(1)).dt.weekindex
#     axs[0].yaxis.set_minor_formatter(dates.DateFormatter('%d-%b'))
    axs[0].yaxis.set_major_locator(dates.MonthLocator())
    axs[0].yaxis.set_major_formatter(dates.DateFormatter('%b-%Y'))
    axs[-1].set_title("Summary")
#     plt.legend(loc=(1.02,.8),frameon=False,fontsize=10)
    """
        lgnd= plt.legend(
        handles=handles,
        labels=labels,
        loc=(1.02,.1),
        frameon=False,
        fontsize=14
    )
    """

    """
    xlabel_text = plt.text(
        -2, -.1, 
        xlabel, 
        horizontalalignment='center',
        verticalalignment='center', 
        transform=ax.transAxes
    )
    """
    plt.tight_layout()
    plt.savefig(filename) # , bbox_extra_artists=(lgnd,), bbox_inches='tight')
    return handles,labels

def compute_sum_plot_bias(df, sel_cols):
    tmp_df = df[
        [s for s in sel_cols if s in df.columns] + 
        [s+'_var' for s in sel_cols if s in df.columns] +
        [s+'_count' for s in sel_cols if s in df.columns]]
    last_valid_index = tmp_df.last_valid_index()
    tmp_df = tmp_df[tmp_df.index <= last_valid_index]
    tmp_df['week'] = tmp_df.index
    tmp_df['week'] = tmp_df['week'].dt.quarter
    gp_rst = tmp_df.groupby('week')
    y_values = tmp_df.index
    for s in sel_cols:
        tmp_df[s] = gp_rst[s].ffill()
        tmp_df[s+'_var'] = gp_rst[s+'_var'].ffill()
        tmp_df[s+'_count'] = gp_rst[s+'_count'].ffill()
    x_axis_val = tmp_df[[s for s in sel_cols]].mean(axis=1, skipna=True)

    mask = np.isfinite(x_axis_val)
    x_axis_val = x_axis_val[mask]
    tmp_date = y_values[mask]
    return x_axis_val, None, tmp_date
