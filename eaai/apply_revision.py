"""
Apply the language and protocol revisions to manuscript.tex and manuscript_anonymous.tex.
Every replacement must match exactly once, so a changed source stops the script.

    python eaai/apply_revision.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import new_results as nr

EDITS = []


def edit(old, new):
    EDITS.append((old, new))


# ── abstract ─────────────────────────────────────────────────────────────────
edit("while two otherwise sensible checks, a mixed-group validation score and the particular scale-invariant XGBoost baseline tested here, remain healthy.",
     "while the particular scale-invariant XGBoost baseline tested here remains healthy and a pooled validation score shows the damage only in part.")

# ── introduction ─────────────────────────────────────────────────────────────
edit("It's a screen we have made. It revealed a failure that we believe is much more than astrodynamics related.",
     "We built such a screen. Building it exposed a failure that we expect to apply beyond astrodynamics.")
edit("This paper deals with that failure. Grouped data was used for training the model and a single feature scaler was fitted for the entire group. It ended up emitting a single constant per group. It's not the surprising part that it happened. What's most interesting is the length of time it took to be noticed. With a mixed validation set it looked fine, since a model can score well if it differentiates groups but cannot differentiate anything within the groups, and validation AUC remained high. A baseline run was executed with a gradient boosted model, with almost perfect results, because the trees divide on the actual values and the scaling on which the network depends is not important to them. Both of the tests we would have used would have told us that the pipeline was healthy.",
     "This paper deals with that failure. A single feature scaler was fitted to grouped data and used to train the model, and the model then produced a single constant output per group. That a pooled scaler can do this is not surprising. The difficulty is that it is easy to miss. A pooled validation score shows the damage only in part: in the controlled ablation below, the AUC over the three targets of a group falls from 0.9995 to 0.875, while the AUC of the failed target alone is 0.687. A gradient boosted baseline on the same transformed arrays gave almost perfect results, because trees split on the values of the features and the rescaling on which the network depends does not matter to them.")
edit("This isn't, of course, comfortable, as running a simple baseline is good advice.",
     "Running a simple baseline is standard advice, and the result above is in tension with it.")
edit("Someone could say that this is only a bad scaling choice. It is, and the fix is easy. The fix is not what we are writing about. We are writing about how this failure hides. The usual validation does not show it, and the usual baseline cannot show it. We describe the failure, show why those two checks miss it, and give a check that does not miss it.",
     "The failure can be described as a preprocessing error, and its remedy, scaling each group separately, is simple. The contribution of this paper is not the remedy. It is the characterization of a failure that a pooled validation score shows only in part and that the tested scale-invariant baseline does not show, together with a check on the spread of the predictions that does show it.")
edit("Its threshold is set on validation runs and tested on runs it has not seen.",
     "Its threshold is set on validation predictions and applied to test predictions, and Section~\\ref{sec:check} states which choices were made after the results were seen.")

# ── related work ─────────────────────────────────────────────────────────────
edit("This type of model simply memorizes the difference, and has validation AUC of $>$0.95 but performs no better inside individual groups. That's what we saw.",
     "This type of model can memorize the difference between groups, and can reach a high AUC on a mixed validation set while performing no better inside individual groups. In our ablation the pooled AUC of the inner group falls to 0.875, while the AUC of Venus alone is 0.687 (Section~\\ref{sec:check}).")

# ── setup ────────────────────────────────────────────────────────────────────
edit("The third setting isn't a straw man, and here's why. You get a single RobustScaler from nearly all the standard pipeline tutorials, applied to a concatenated training set. No warning is issued and it looks like a normalised array.",
     "The third setting is not an artificial construction. A single RobustScaler fitted to a concatenated training set is what many standard preprocessing tutorials produce. It raises no warning, and the result looks like an ordinary normalised array.")

# ── section IV ───────────────────────────────────────────────────────────────
edit("This is used as the signal ratio, defined as the average of the standard deviation of the normalised features across missions, calculated only in the observed window. It's not a limitation you would expect but it does matter. The metric is totally useless averaged over the entire flight, because late timesteps have a huge spread across missions, as the missions that fail have physically diverged by that time, and that spread swamps the early signal so that all conditions appear healthy. The model commits at 40\\%, so what's important is the range within the prefix the model observes.",
     "We use the signal ratio, defined as the average standard deviation of the normalised features across missions, calculated only in the observed window. The window matters. Averaged over the entire flight the metric is uninformative: late timesteps have a large spread across missions, because the missions that fail have physically diverged by then, and this spread swamps the early signal, so that all conditions appear alike. The model commits at 40\\%, so the relevant range is the one inside the prefix that the model observes.")
edit("The first result is the decomposition that is controlled. The network is able to operate with the signal being reduced by up to a factor of 23 by pooling across time in a single target. It works on all 4 targets, with a loss of a few thousandths of AUC at most. Another kettle of fish is the pooling of a group. On Venus, the output standard deviation is 3.11e-05, which is one number for every mission, and the AUC drops from 0.9999 to 0.6037.",
     "The first result is a controlled decomposition. Pooling across time within a single target reduces the signal by up to a factor of 23, and the network still works on all 4 targets, with a loss of a few thousandths of AUC at most. In contrast, pooling feature statistics across heterogeneous target groups produces substantially more severe degradation, including near-constant predictions for Venus: the output standard deviation is 3.11e-05, which is one value for every mission, and the AUC drops from 0.9999 to 0.6037.")
edit("The term `collapse' is used instead of `underfitting' because of Fig.~\\ref{fig:venus}. A low AUC on its own doesn't mean much, because that is what you would get if the model learned something poor or wrong. A distribution on unseen missions that is three ten-thousandths wide is not ambiguous at all. The network is no longer under the control of its input.",
     "We use the term `collapse' and not `underfitting' because of Fig.~\\ref{fig:venus}. A low AUC alone is ambiguous, since it is also produced by a model that has learned something poor or wrong. A predicted distribution on unseen missions that is three ten-thousandths wide is not ambiguous: the output no longer depends on the input.")
edit("This is because Jupiter's task is nicely split up so that even a very weak signal is sufficient.",
     "One explanation is that the Jupiter task is easily separable, so that even a very weak signal is sufficient. We did not test this directly.")
edit("This is the methodological part and it's crucial to pay attention to the exact claim.",
     "The exact claim matters here.")
edit("Accuracy on a mixed validation set does not catch the collapse, because a per group constant ranks the groups correctly and a pooled metric rewards that. It's picked up by two checks.",
     "A pooled validation score shows the collapse only in part. For the inner group (Mercury, Venus and Mars) the AUC over all three targets falls from 0.9995 to 0.875 under grouped normalisation, while the AUC of Venus alone is 0.687, because a model that is constant within each group still ranks the groups against each other. The pooled value is higher than the value for the worst target and does not say which target failed. Two checks identify it.")
edit("exposes four near-constant Venus runs that a pooled AUC and the tested XGBoost comparison do not identify.",
     "exposes four near-constant Venus runs that the tested XGBoost comparison does not identify and that a pooled AUC shows only in part.")
edit("\\textbf{Demonstrated result.}",
     "The first paragraph below states what the experiments in this paper show. The second and third describe consequences and a workflow that have not been tested.\n\n\\textbf{Demonstrated result.}")

# ── section VI: protocol ─────────────────────────────────────────────────────
edit(" A run counts as collapsed if its AUC on that split is 0.85 or lower. That cutoff sits in the biggest gap in the data: four runs fall between 0.51 and 0.82, and the rest are at 0.895 or above.",
     " A run counts as collapsed if its AUC on that split is 0.85 or lower.")

PROTOCOL = r"""The choices in this evaluation were made in the following order. The group definitions and the three normalisation settings come from the ablation of Section~\ref{sec:collapse}. The AUC cutoff of 0.85 that defines a collapsed run was set after the validation and the test AUCs of all 60 runs had been seen. It was placed in the largest gap of the test AUCs (0.82 to 0.895) and of the validation AUCs (0.81 to 0.907). It was therefore not chosen in advance, and test results influenced it. Given the cutoff, the spread threshold was chosen on validation predictions and validation AUCs only. It is the middle, on a log scale, of the gap between the largest $S$ of a collapsed run (1.0e-04) and the smallest $S$ of a working run (0.071), which is 2.7e-03. The test predictions and test AUCs were used afterwards, to count the flagged runs. At this cutoff the threshold flags 4 runs out of 60, and those are the 4 with a test AUC of 0.85 or lower. No working run is flagged. $D$, with its threshold chosen the same way, flags the same 4. Because of the way the cutoff was chosen, this result is a check of the threshold and not an independent test of the cutoff."""
edit("We chose the threshold on the validation predictions only. It is the middle, on a log scale, of the gap between the largest $S$ of a collapsed run (1.0e-04) and the smallest $S$ of a working run (0.071), which is 2.7e-03. Then we applied it, unchanged, to the test predictions. It flags 4 runs out of 60, and those are exactly the 4 that collapsed. No working run is flagged. $D$, with its threshold chosen the same way, flags the same 4. So the reference model did not add anything here.",
     PROTOCOL + " The reference model did not add anything here.")

edit(" It is above the threshold and is not flagged. If a run is called collapsed at AUC 0.90 and not 0.85, there are 5 collapsed runs and the ROC AUC of $S$ is 0.993 and not 1.000.",
     " It is above the threshold and is not flagged.")

TABLE = ("\\begin{table*}[t]\n\\centering\n"
         "\\caption{Dependence on the AUC cutoff that defines a collapsed run. Collapsed runs are counted on validation and on test. The threshold is set on validation only, and `none' means that the labelled groups overlap on validation. Missed runs and false alarms are counted on test. The last four columns give the ROC AUC, on test, of four label-free summaries of the predictions.}\n"
         "\\label{tab:cutoffs}\n\\footnotesize\n\\begin{tabular}{@{}ccccccccc@{}}\n\\toprule\n"
         "Cutoff & Collapsed (val/test) & Threshold & Missed & False alarms & $S$ & IQR & Range & Entropy \\\\\n\\midrule\n"
         + nr.protocol_table() + "\n\\bottomrule\n\\end{tabular}\n\\end{table*}\n\n")

SWEEP = r"""Table~\ref{tab:cutoffs} shows how the result depends on the cutoff. A single threshold can be set on the validation runs only at cutoffs of 0.85 and 0.90. Below 0.85 the Venus run on seed 2, with a validation AUC of 0.81, is labelled as working, but its spread (7.9e-05) lies inside the range of the collapsed runs, so no threshold separates the two labelled groups. At 0.95 fourteen runs count as collapsed, including Mercury runs that keep their spread, and the groups overlap again. The ranking is more stable than the threshold: the ROC AUC of $S$ on the test predictions is 1.000 for every cutoff from 0.60 to 0.85 and 0.993 at 0.90. We read this as follows. The score separates runs with a near-constant output from the other runs. Whether a run with a constant output but a usable ranking, such as Venus on seed 2, is called collapsed depends on the AUC cutoff.

To test the threshold on seeds it was not chosen on, we set it on the validation predictions of four seeds and applied it to the test predictions of the fifth, for each seed in turn. At a cutoff of 0.85 this gives 4 collapsed runs, 0 missed and 0 false alarms over the 60 runs. At 0.90 there are 5 collapsed runs, 1 missed (a Mercury run that keeps its spread) and 0 false alarms. At the lower cutoffs no threshold could be set on some of the seeds, for the reason given above. These seeds redraw the split and the initialisation, but they use the same four targets, so this is not a test on new targets.

The statistic is an ordinary output variance, and we do not claim that it is the best summary. Table~\ref{tab:cutoffs} also gives the ROC AUC of three other label-free summaries of the same predictions: the interquartile range, the range, and the mean binary entropy. Up to a cutoff of 0.85 all of them separate the collapsed runs well (0.98 to 1.00). At 0.90 the spread score is the highest (0.993, against 0.989 for the entropy, 0.978 for the range and 0.945 for the interquartile range), and at 0.95 the range and the entropy are higher than it. The differences are small and rest on four collapsed runs from one target. What these results support is that a summary of the predictions per group detects a failure that the tested XGBoost baseline does not detect and that a pooled score shows only in part. They do not support a claim that this score is better than other output summaries.

A pooled score shows the collapse only in part. For the inner group (Mercury, Venus and Mars) the AUC over the test missions of all three targets is 0.9995 per timestep and 0.875 under grouped normalisation, averaged over the five seeds. That is a visible drop. It is, however, 0.19 above the AUC of Venus alone (0.687), and above the mean of the three per target AUCs (0.845), because a model that is constant within a group still ranks the groups against each other. The pooled value also does not say which target failed. The spread is computed per target, and it is 3.1e-05 to 9.7e-05 for the four collapsed Venus runs, against 0.7 or more for Mercury and Mars under grouped normalisation.

"""
edit("\\begin{table}[t]\n\\centering\n\\caption{The 60 runs by state.", TABLE + "\\begin{table}[t]\n\\centering\n\\caption{The 60 runs by state.")

BATCH = r"""The spread is computed over a batch of predictions, so it depends on the batch size and on how the probabilities are calibrated. We resampled the saved test predictions at random. Batches of 30 or more missions flagged every collapsed run and no working run. Batches of 10 flagged 1.1\% of the working batches and batches of 5 flagged 7.4\%. These batches contain both outcomes, because they were drawn at random from the test missions. A batch that holds missions of one outcome only, or from one narrow region of the input space, was not tested, and a small spread would be expected there. We also rescaled the predicted log-odds by a temperature from 0.25 to 4. The smallest spread of a working run then moved between 0.28 and 0.018, and the threshold of 2.7e-03 still separated the 4 collapsed runs from the 56 working runs. This is a monotone change of the outputs of one model family. A model with different calibration, architecture, label prevalence or batch size needs its own threshold.

"""
edit("The signal ratio of Section~\\ref{sec:collapse} can be measured before any training.", SWEEP + BATCH + "The signal ratio of Section~\\ref{sec:collapse} can be measured before any training.")

# ── limitations ──────────────────────────────────────────────────────────────
edit("\\item Threshold. The cutoff that defines a collapsed run (AUC of 0.85 or lower) was chosen after the results were seen, from the largest gap in the data. The spread threshold (2.7e-03) was then set on validation predictions only and applied to the test predictions, so the test result is a check of that threshold and not a pre-registered test. All 4 collapsed runs are Venus, so only one kind of collapse has been tested. The threshold is not expected to transfer unchanged to another dataset, model architecture, output calibration, target group, prevalence or batch size. A new setting needs labelled development runs to calibrate it and an untouched test to evaluate it. The spread statistic itself needs no labels at inference time.",
     "\\item Threshold. The AUC cutoff that defines a collapsed run (0.85) was set after the validation and test AUCs had been seen. The spread threshold (2.7e-03) was chosen on validation predictions only, so the test result is a check of that threshold and not an independent test of the cutoff. A single threshold can be set only for cutoffs of 0.85 and 0.90. All 4 collapsed runs are Venus, so one kind of collapse has been tested. The threshold is not expected to transfer unchanged to another dataset, model architecture, output calibration, target group, prevalence or batch size, and batches with one outcome class were not tested. A new setting needs labelled development runs to calibrate it and an untouched test to evaluate it. The spread statistic itself needs no labels at inference time.")


def main():
    for name in ("manuscript.tex", "manuscript_anonymous.tex"):
        path = HERE / name
        s = path.read_text()
        for old, new in EDITS:
            if s.count(old) != 1:
                raise SystemExit(f"{name}: expected one match, found {s.count(old)} for: {old[:70]!r}")
            s = s.replace(old, new)
        path.write_text(s)
        print(name, "patched", len(EDITS), "edits")


if __name__ == "__main__":
    main()
