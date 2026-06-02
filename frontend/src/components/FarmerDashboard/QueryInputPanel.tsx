import React, { useState } from 'react';
import type { TicketCreateRequest } from '../../api/tickets';

interface QueryInputPanelProps {
  onSubmit: (query: TicketCreateRequest) => void;
  isLoading: boolean;
}

export const QueryInputPanel: React.FC<QueryInputPanelProps> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<TicketCreateRequest>({
    farmer_name: 'Teja Prasad',
    farmer_email: 'teja.behara@amzur.com',
    query: '',
    crop_type: 'tomato',
    location: 'Andhra Pradesh',
    weather: 'humid',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.query.trim() && !isSubmitting && !isLoading) {
      setIsSubmitting(true);
      onSubmit(formData);
      setFormData((prev) => ({
        ...prev,
        query: '',
      }));
      // Reset after mutation completes (3.5s for toast + buffer)
      setTimeout(() => setIsSubmitting(false), 4000);
    }
  };

  return (
    <div className="mb-6 rounded-3xl border border-slate-200 bg-white/95 p-6 shadow-sm backdrop-blur">
      <h2 className="text-xl font-semibold tracking-tight text-slate-900">Create Ticket</h2>
      <p className="mb-4 text-sm text-slate-500">Creates OPEN ticket and pauses workflow for admin approval.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Farmer Name</label>
            <input
              type="text"
              name="farmer_name"
              value={formData.farmer_name}
              onChange={handleChange}
              placeholder="Farmer full name"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Farmer Email</label>
            <input
              type="email"
              name="farmer_email"
              value={formData.farmer_email}
              onChange={handleChange}
              placeholder="farmer@example.com"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Crop Type</label>
            <select
              name="crop_type"
              value={formData.crop_type}
              onChange={handleChange}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            >
              <option value="tomato">Tomato</option>
              <option value="rice">Rice</option>
              <option value="wheat">Wheat</option>
              <option value="corn">Corn</option>
              <option value="cotton">Cotton</option>
              <option value="sugarcane">Sugarcane</option>
              <option value="potato">Potato</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Location</label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g., Andhra Pradesh"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Weather</label>
            <select
              name="weather"
              value={formData.weather}
              onChange={handleChange}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            >
              <option value="sunny">Sunny</option>
              <option value="rainy">Rainy</option>
              <option value="humid">Humid</option>
              <option value="dry">Dry</option>
              <option value="cloudy">Cloudy</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Farmer Query</label>
          <textarea
            name="query"
            value={formData.query}
            onChange={handleChange}
            placeholder="Describe your farming problem or concern... e.g., 'My tomato leaves are turning yellow'"
            className="h-24 w-full resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
          />
          <p className="text-xs text-slate-500 mt-1">This creates an OPEN ticket and stores workflow pause details.</p>
        </div>

        <button
          type="submit"
          disabled={isLoading || isSubmitting || !formData.query.trim() || !formData.farmer_name.trim() || !formData.farmer_email.trim()}
          className="w-full rounded-xl bg-sky-600 px-4 py-2.5 font-semibold text-white shadow-sm transition duration-200 hover:bg-sky-700 hover:shadow disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isLoading || isSubmitting ? 'Creating Ticket...' : 'Create Ticket'}
        </button>
      </form>
    </div>
  );
};
