class Action:
    INCOME = "income"
    FOREIGN_AID = "foreign_aid"
    COUP = "coup"
    TAX = "tax"
    ASSASSINATE = "assassinate"
    STEAL = "steal"
    EXCHANGE = "exchange"
    BLOCK_FOREIGN_AID = "block_foreign_aid"
    BLOCK_STEAL = "block_steal"
    BLOCK_ASSASSINATE = "block_assassinate"
    CHALLENGE = "challenge"

    PRIMARY_ACTIONS = [INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE]
    BLOCK_ACTIONS = [BLOCK_FOREIGN_AID, BLOCK_STEAL, BLOCK_ASSASSINATE]