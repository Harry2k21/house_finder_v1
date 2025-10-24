const axios = require('axios');

test('Scrape endpoint pulls the result amount', async () => {
  const testUrl = 'https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=Barnsley%2C+South+Yorkshire&useLocationIdentifier=true&locationIdentifier=REGION%5E108&rent=To+rent&radius=40.0&_includeLetAgreed=on&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=Barnsley.html';
  const response = await axios.get(`http://127.0.0.1:5000/scrape?url=${encodeURIComponent(testUrl)}`);
  
  expect(response.status).toBeLessThan(500);
  expect(response.data).toHaveProperty('results');
});


