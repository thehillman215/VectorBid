import SettingsLayout from '../../components/SettingsLayout';

const BillingSettings = () => (
  <SettingsLayout>
    <h1>Billing History</h1>
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Description</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td colSpan={3}>No billing records found.</td>
        </tr>
      </tbody>
    </table>
  </SettingsLayout>
);

export default BillingSettings;
