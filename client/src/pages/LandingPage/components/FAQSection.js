// client/src/pages/LandingPage/components/FAQSection.js
import React from 'react';
import './FAQSection.css';

function FAQSection({ id }) {
  const faqs = [
    {
      question: "What kind of photos should I upload for my child's AI photoshoot?",
      answer:
        "Aim for variety. Include different angles, facial expressions, and backgrounds. Avoid heavy makeup or large accessories. The more unique photos you provide, the richer the final AI-generated photoshoot becomes."
    },
    {
      question: "How do you handle the photos I upload?",
      answer:
        "We use your child's photos only to train our AI model. Once the model is generated, we securely delete those original images—within a few days or immediately upon your request."
    },
    {
      question: "Who owns the AI photoshoot results?",
      answer:
        "You do! We grant full commercial rights and ownership of your AI-generated images. Share them on social media, print them for family, or use them anywhere else you like."
    },
    {
      question: "What if I don’t like any of the generated photos?",
      answer:
        "If you’re truly unhappy and can’t find a single ‘keeper,’ we’ll offer a re-run or a full refund. We want you to love your AI photoshoot results."
    },
    {
      question: "Is it safe to upload kids’ photos? Are prompts moderated?",
      answer:
        "Yes. Child privacy and safety are top priorities. We closely monitor prompts and secure your uploads so they remain private. Inappropriate requests are blocked."
    },
    {
      question: "How long does it usually take?",
      answer:
        "Most photoshoots finish within a few hours. This may vary slightly depending on server load, but same-day results are typical."
    },
    {
      question: "How secure is the payment process?",
      answer:
        "We partner with Stripe, a reputable payment provider that uses bank-level encryption. We never store your card details on our servers."
    },
    {
      question: "Which payment methods do you accept?",
      answer:
        "We accept major credit or debit cards (Visa, MasterCard, AmEx), as well as certain regional payment methods like iDeal or Bancontact. We do not currently accept PayPal or cryptocurrency."
    },
    {
      question: "Can I delete the AI photos or my child's uploaded pictures afterward?",
      answer:
        "Absolutely. You can remove individual uploads at any time, and we permanently delete them from our servers. If you have any concerns, just let us know."
    },
    {
      question: "Are these AI photos suitable for social media or professional use?",
      answer:
        "Yes! Many parents share them on personal Instagram feeds or even use them for family gifts. They’re high-resolution and perfect for both casual and professional settings."
    }
  ];

  return (
    <section  id={id} className="faq-section">
      <div className="faq-inner">
        <h2 className="section-title">Frequently Asked Questions</h2>
        <p className="section-subtitle">
          Learn more about our AI-powered photoshoot process, child safety, and how
          you can make the most of your final images.
        </p>

        <div className="faqs-container">
          {faqs.map((item, index) => (
            <div className="faq-item" key={index}>
              <h3 className="faq-question">{item.question}</h3>
              <p className="faq-answer">{item.answer}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FAQSection;