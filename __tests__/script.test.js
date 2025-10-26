/**
 * @jest-environment jsdom
 */

const axios = require('axios');

// Mock localStorage and load script for frontend tests
// Mock localStorage
global.localStorage = {
  getItem: jest.fn(() => '[]'),
  setItem: jest.fn(),
};


let count = 0;
const maxRequirements = 20;

function addRequirement(text = "", checked = false) {
  if (count >= maxRequirements) return;
  count++;

  const list = document.getElementById("list");
  const reqDiv = document.createElement("div");
  reqDiv.className = "requirement";

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.checked = checked;

  const textInput = document.createElement("input");
  textInput.type = "text";
  textInput.placeholder = "Enter requirement...";
  textInput.value = text;

  const delBtn = document.createElement("button");
  delBtn.textContent = "❌";

  reqDiv.appendChild(checkbox);
  reqDiv.appendChild(textInput);
  reqDiv.appendChild(delBtn);
  list.appendChild(reqDiv);
}

test('Scrape endpoint pulls the result amount', async () => {
  const testUrl = 'https://www.rightmove.co.uk/property-to-rent/find.html?searchLocation=Barnsley%2C+South+Yorkshire&useLocationIdentifier=true&locationIdentifier=REGION%5E108&rent=To+rent&radius=40.0&_includeLetAgreed=on&index=0&sortType=6&channel=RENT&transactionType=LETTING&displayLocationIdentifier=Barnsley.html';
  const response = await axios.get(`http://127.0.0.1:5000/scrape?url=${encodeURIComponent(testUrl)}`);
  
  expect(response.status).toBeLessThan(500);
  expect(response.data).toHaveProperty('results');
});

test('Add Requirement btn adds a input', async () => {
  count = 0;
  document.body.innerHTML = `<div id="list"></div><button id="addBtn"></button>`;
  addRequirement();
  expect(document.querySelectorAll('.requirement').length).toBe(1);
});