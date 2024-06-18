import pandas as pd

# read in log csv
log_file = "./logs-insights.csv"  # path to logs as .csv
logs = pd.read_csv(log_file)

messages = [eval(result.strip('Message: "Validation error: ')) for result in logs["@message"]]
messages = pd.DataFrame([result for result in messages if isinstance(result, dict)])


# clean data
def convert_error_type_to_reason(message):
    error_type_to_reason = {
        "NonNullableConstraintFailure": "Cell left empty",
        "WrongTypeFailure": "Invalid data entered",
        "NonUniqueCompositeKeyFailure": "Duplicate data entered",
        "InvalidEnumValueFailure": "Invalid dropdown value entered",
    }

    if message["error_type"] in ["TownsFundRoundFourValidationFailure", "GenericFailure"]:
        if "CDEL" in message["description"] or "RDEL" in message["description"]:
            return "Allocated funding exceeded"
        elif "postcode" in message["description"]:
            return error_type_to_reason["WrongTypeFailure"]
        elif "blank" in message["description"]:
            return error_type_to_reason["NonNullableConstraintFailure"]
        elif "entered your own content" in message["description"]:
            return error_type_to_reason["InvalidEnumValueFailure"]
        else:
            return "Generic error"
    else:
        return error_type_to_reason[message["error_type"]]


messages["reason"] = messages.apply(convert_error_type_to_reason, axis=1)

# generate plots
group_by_error = messages.groupby("reason").count()["sheet"].sort_values(ascending=False)
print(group_by_error)
error_pie = group_by_error.plot.pie(autopct="%1.1f%%", title="Reasons for validation errors", label="")
fig = error_pie.get_figure()
fig.savefig("validation_error_reasons.png", bbox_inches="tight")
fig.show()  # flushes current fig from figure so the next one isn't rendered on top

group_by_tab = messages.groupby("sheet").count()["section"].sort_values(ascending=False)
print(group_by_tab)
tab_pie = group_by_tab.plot.pie(autopct="%1.1f%%", title="Validation errors per spreadsheet tab", label="")
fig = tab_pie.get_figure()
fig.savefig("validation_errors_per_tab.png", bbox_inches="tight")
fig.show()

group_by_tab_error = messages.groupby(["sheet", "reason"]).count()["section"].unstack("reason")
error_tab_bar = group_by_tab_error.plot.bar(title="Validation error types per spreadsheet tab", width=1)
fig = error_tab_bar.get_figure()
fig.savefig("validation_error_reasons_per_tab.png", bbox_inches="tight")
fig.show()
