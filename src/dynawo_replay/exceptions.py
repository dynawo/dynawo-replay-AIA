class DynawoExecutionError(Exception):
    "Indicates an error during Dynaωo execution."


class CaseNotPreparedForReplay(Exception):
    "Indicates that the case is not ready for replay due to missing data."


class NotStabilizedCurve(Exception):
    "Indicates that a curve does not meet the stabilization criteria."


class UnresolvedReference(Exception):
    "Indicates that a reference in the parameter set is missing in dumpInit."


class NotSupportedModel(Exception):
    "Indicated that the model is not supported for local replay"
