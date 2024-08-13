# Funeral Admin Application

The Funeral Admin Application is a web-based platform designed to facilitate funeral cover management and funeral home administration. It offers a comprehensive set of features for both users and administrators, allowing for seamless policy management, claims processing, and funeral arrangement assistance.

## Features

### For Users:
- **Policy Registration**: Users can register for funeral cover plans online, choosing from a range of options based on their needs.
- **Premium Payments**: Convenient online payment options are available for users to pay their premiums securely.
- **Claims Processing**: Users can file claims online and track the status of their claims through the platform.
- **Funeral Arrangement Assistance**: Resources and support are provided to assist users in arranging funeral services and ceremonies.

### For Administrators:
- **Policy Management**: Administrators can manage user accounts, policies, premiums, and claims through a centralized dashboard.
- **Claims Processing**: Streamlined workflow for verifying and processing claims, ensuring efficient handling of user requests.
- **Funeral Home Integration**: Partnerships with funeral homes allow for seamless coordination of funeral arrangements and services.
- **Reporting and Analytics**: Reporting tools provide insights into policy uptake, claim frequency, and financial performance.

## Classes

### PolicyRegistrationData:
- uid: str
- branch_uid: str
- company_uid: str
- policy_number: str
- total_family_members: int
- total_premiums: int
- payment_code_reference: str
- date_activated: str
- first_premium_date: str
- payment_day: int
- client_signature: str
- employee_signature: str
- plan_choice_name: str
- payment_method: str
- relation_to_policy_holder: str
- policy_active: bool
- is_policy_holder: bool

### Claims:
- uid: str
- branch_uid: str
- company_uid: str
- claim_amount: int
- claim_total_paid: int
- claimed_for_uid: str
- date_paid: str
- claim_status: str
- funeral_company: str
- claim_type: str

### CoverPlanDetails:
- branch_id: str
- company_id: str
- plan_name: str
- plan_type: str
- benefits: List[str]
- coverage_amount: int
- premium_costs: int
- additional_details: str
- terms_and_conditions: str
- inclusions: List[str]
- exclusions: List[str]
- contact_information: str
- policy_registration_data: PolicyRegistrationData

## Usage

1. **Installation**: Clone the repository and install the required dependencies using `pip install -r requirements.txt`.
2. **Configuration**: Set up database connections, authentication, and environment variables as per the provided configuration files.
3. **Deployment**: Deploy the application to your preferred web hosting platform.
4. **Usage**: Access the web application through a supported web browser and begin using the funeral admin features.

## Contributing

Contributions to the Funeral Admin Application are welcome! Please refer to the contribution guidelines for more information on how to get started.

## License

This project is licensed under the [MIT License](LICENSE).
